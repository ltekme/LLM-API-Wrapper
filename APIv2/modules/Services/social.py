import typing as t
import sqlalchemy.orm as so

from .Base import ServiceBase
from .User.User import UserService
from ..FacebookClient import FacebookClient
from ..ApplicationModel import SocialsProfileProvider, UserSocialProfile, User
from ..exception import AuthorizationError

from APIv2.logger import logger


class SocialProviderService(ServiceBase):
    def __init__(self, dbSession: so.Session) -> None:
        super().__init__(dbSession, serviceName="SocialProviderService")

    def getByName(self, name: str) -> t.Optional[SocialsProfileProvider]:
        """
        Get a social provider by name.
        :param name: The name of the social provider.
        :return: The social provider instance.
        """
        return self.dbSession.query(SocialsProfileProvider).where(SocialsProfileProvider.name == name).first()

    def createByName(self, name: str) -> SocialsProfileProvider:
        """
        Create a social provider by name.
        :param name: The name of the social provider.
        :return: The social provider instance.
        """
        instance = SocialsProfileProvider(name)
        self.dbSession.add(instance)
        return instance

    def getOrCreateByName(self, name: str) -> SocialsProfileProvider:
        """
        Get or create a social provider by name.
        :param name: The name of the social provider.
        :return: The social provider instance.
        """
        instance = self.getByName(name)
        if instance is not None:
            return instance
        return self.createByName(name)


class SocialProfileService(ServiceBase):

    def __init__(self, dbSession: so.Session) -> None:
        super().__init__(dbSession, serviceName="SocialProfileService")

    def get(self, socialId: str, provider: SocialsProfileProvider) -> t.Optional[UserSocialProfile]:
        """
        Get a social profile.
        :param socialId: The social ID of the user.
        :param provider: The social provider instance.
        :return: The user social profile instance.
        """
        return self.dbSession.query(UserSocialProfile).where(
            UserSocialProfile.socialId == socialId,
            UserSocialProfile.provider == provider,
        ).first()

    def create(self, socialId: str, provider: SocialsProfileProvider, name: t.Optional[str] = None) -> UserSocialProfile:
        """
        Create a social profile.
        :param socialId: The social ID of the user.
        :param provider: The social provider instance.
        :return: The user social profile instance.
        """
        instance = UserSocialProfile(socialId=socialId, provider=provider)
        instance.socialName = name
        self.dbSession.add(instance)
        return instance

    def getOrCreate(self, socialId: str, provider: SocialsProfileProvider, name: t.Optional[str] = None) -> UserSocialProfile:
        """
        Get or create a social profile.
        :param socialId: The social ID of the user.
        :param provider: The social provider instance.
        :return: The user social profile instance.
        """
        instance = self.get(socialId, provider)
        if instance is not None:
            return instance
        return self.create(socialId, provider, name)

    def associateUser(self, socialProfile: UserSocialProfile, user: User) -> None:
        """
        Associate a social profile with a user profile.
        :param socialProfile: The social profile instance.
        :param profile: The user profile instance.
        """
        socialProfile.user = user


class FacebookService(ServiceBase):

    providerName = "Facebook"

    def __init__(self, dbSession: so.Session, userService: UserService, socialProfileService: SocialProfileService, socialProviderService: SocialProviderService, facebookClient: FacebookClient) -> None:
        super().__init__(dbSession, serviceName="FacebookService")
        self.userService = userService
        self.socialProfileService = socialProfileService
        self.socialProviderService = socialProviderService
        self.facebookClient = facebookClient

    @property
    def provider(self) -> SocialsProfileProvider:
        """
        Get the social provider instance.
        :return: The social provider instance.
        """
        return self.socialProviderService.getOrCreateByName(self.providerName)

    def getOrCreateSocialProfileFromAccessToken(self, accessToken: str) -> UserSocialProfile:
        """
        Get or create a user from Focabook social profile from access token.
        :param accessToken: The access token of a given Facebook user.
        :return: The user social profile instance.
        """
        try:
            facebookProfile = self.facebookClient.getUsernameAndId(accessToken=accessToken)
        except Exception as e:
            logger.error(f"Error performing user identification, {e}")
            raise AuthorizationError("Error performing facebook user identification")
        provider = self.socialProviderService.getOrCreateByName(self.providerName)
        return self.socialProfileService.getOrCreate(str(facebookProfile.facebookId), provider, facebookProfile.username)

    def getOrCreateUserProfileFromAccessToken(self, accessToken: str) -> User:
        """
        Get a user profile from Facebook access token.
        :param accessToken: The access token of a given Facebook user.
        :param userService: The user service instance.
        :return: A new instance of UserSocialProfile with Id and username populated.
        """
        socialProfile = self.getOrCreateSocialProfileFromAccessToken(accessToken)
        if socialProfile.user is not None:
            return socialProfile.user
        if socialProfile.socialName is None:
            userProfile = self.userService.createAnonymous()
        else:
            userProfile = self.userService.createUser(socialProfile.socialName)
        self.socialProfileService.associateUser(socialProfile, userProfile)
        return userProfile
