/**
 * Copyright(c) Live2D Inc. All rights reserved.
 *
 * Use of this source code is governed by the Live2D Open Software license
 * that can be found at https://www.live2d.com/eula/live2d-open-software-license-agreement_en.html.
 */

import { CubismMatrix44 } from "../Live2DFramework/src/math/cubismmatrix44";
import { ACubismMotion } from "../Live2DFramework/src/motion/acubismmotion";
import { csmVector } from "../Live2DFramework/src/type/csmvector";

import * as Define from "./Define";
import { canvas } from "./Delegate";
import { Model } from "./Model";
import { Pal } from "./Pal";

export class Live2DManager {
  private static s_instance: Live2DManager | null = null;
  _viewMatrix: CubismMatrix44 = new CubismMatrix44();
  _models: csmVector<Model> = new csmVector<Model>(); // get this ?
  _sceneIndex: number = 0;

  constructor() {
    this.changeScene(this._sceneIndex);
  }

  public static getInstance(): Live2DManager {
    if (this.s_instance === null) {
      this.s_instance = new Live2DManager();
    }

    return this.s_instance;
  }

  public static releaseInstance(): void {
    if (this.s_instance !== null) {
      // this.s_instance = void 0;
      this.s_instance = null;
    }

    this.s_instance = null;
  }

  public getModel(no: number): Model | null {
    if (no < this._models.getSize()) {
      return this._models.at(no);
    }

    return null;
  }

  public setMouthValueCallback(func: () => number): void {
    for (let i = 0; i < this._models.getSize(); i++) {
      this._models.at(i).setMouthValueCallback(func);
    }
  }

  public releaseAllModel(): void {
    for (let i = 0; i < this._models.getSize(); i++) {
      this._models.at(i).release();
      this._models.set(i, Model.getInstance()); // null
    }

    this._models.clear();
  }

  public onDrag(x: number, y: number): void {
    for (let i = 0; i < this._models.getSize(); i++) {
      const model: Model | null = this.getModel(i);

      if (model) {
        model.setDragging(x, y);
      }
    }
  }

  public onTap(x: number, y: number): void {
    if (Define.DebugLogEnable) {
      Pal.printMessage(
        `[APP]tap point: {x: ${x.toFixed(2)} y: ${y.toFixed(2)}}`
      );
    }

    for (let i = 0; i < this._models.getSize(); i++) {
      if (this._models.at(i).hitTest(Define.HitAreaNameHead, x, y)) {
        if (Define.DebugLogEnable) {
          Pal.printMessage(`[APP]hit area: [${Define.HitAreaNameHead}]`);
        }
        this._models.at(i).setRandomExpression();
      } else if (this._models.at(i).hitTest(Define.HitAreaNameBody, x, y)) {
        if (Define.DebugLogEnable) {
          Pal.printMessage(`[APP]hit area: [${Define.HitAreaNameBody}]`);
        }
        this._models
          .at(i)
          .startRandomMotion(
            Define.MotionGroupTapBody,
            Define.PriorityNormal,
            this._finishedMotion
          );
      }
    }
  }

  public startVoiceConversation(url: string): void {  // tts live2d speak
    for (let i = 0; i < this._models.getSize(); i++) {
      if (Define.DebugLogEnable) {
        Pal.printMessage(`[Live2dManager][startVoiceConversation]starting with ${url.slice(0, 10)}`);
        this._models.at(i)._wavFileHandler.loadWavFile(url);  // 只有口型?
      };
    }
  }


  public onUpdate(): void {
    if (canvas === null) {
      return;
    }

    const { width, height } = canvas;

    const modelCount: number = this._models.getSize();

    for (let i = 0; i < modelCount; ++i) {
      const projection: CubismMatrix44 = new CubismMatrix44();
      const model: Model | null = this.getModel(i);
      if (model === null) {
        continue;
      }

      if (model.getModel()) {
        if (model.getModel().getCanvasWidth() > 1.0 && width < height) {
          model.getModelMatrix().setWidth(2.0);
          projection.scale(1.0, width / height);
        } else {
          projection.scale(height / width, 1.0);
        }

        if (this._viewMatrix != null) {
          projection.multiplyByMatrix(this._viewMatrix);
        }
      }

      model.update();
      model.draw(projection);
    }
  }

  public nextScene(): void {
    const no: number = (this._sceneIndex + 1) % Define.ModelDirSize;
    this.changeScene(no);
  }

  public changeScene(index: number): void {
    this._sceneIndex = index;
    if (Define.DebugLogEnable) {
      Pal.printMessage(`[APP]model index: ${this._sceneIndex}`);
    }

    const model: string = Define.ModelDir[index];
    const modelPath: string = Define.ResourcesPath + model + "/";
    let modelJsonName: string = Define.ModelDir[index];
    modelJsonName += ".model3.json";

    Pal.printMessage(`[Live2dManager] Attempting to load ${modelPath + modelJsonName}`);

    this.releaseAllModel();
    this._models.pushBack(new Model());
    this._models.at(0).loadAssets(modelPath, modelJsonName);

    Pal.printMessage(`[Live2dManager] Loaded model ${this._models}`);

  }

  public setViewMatrix(m: CubismMatrix44) {
    for (let i = 0; i < 16; i++) {
      this._viewMatrix.getArray()[i] = m.getArray()[i];
    }
  }

  _finishedMotion = (self: ACubismMotion): void => {
    Pal.printMessage(`Motion Finished:`);
  };
}
