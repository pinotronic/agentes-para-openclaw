import type { Sprite } from './Sprite';

export interface AtlasConfig {
  name: string;
  width: number;
  height: number;
  exportMode: 'PNG' | 'JSON' | 'ZIP';
  autoPack: boolean;
  gap: number;
  rotation: boolean;
}

export interface Atlas {
  id: string;
  config: AtlasConfig;
  sprites: Sprite[];
  createdAt: Date;
}

export const MIN_ATLAS_SIZE = 16;
export const MAX_ATLAS_SIZE = 4096;
