export interface SpriteMetadata {
  format: 'PNG' | 'JPEG' | 'WEBP';
  originalSize: number;
}

export interface Sprite {
  id: string;
  name: string;
  width: number;
  height: number;
  sourceUrl: string;
  metadata: SpriteMetadata;
  packedX: number | null;
  packedY: number | null;
  gridIndex: number | null;
  isPacked: boolean;
}

export function validateSpriteDimensions(width: number, height: number): void {
  if (width <= 0) {
    throw new Error('Width must be positive');
  }
  if (height <= 0) {
    throw new Error('Height must be positive');
  }
}

export function createSprite(props: Omit<Sprite, 'packedX' | 'packedY' | 'gridIndex' | 'isPacked'>): Sprite {
  validateSpriteDimensions(props.width, props.height);
  return {
    ...props,
    packedX: null,
    packedY: null,
    gridIndex: null,
    isPacked: false,
  };
}
