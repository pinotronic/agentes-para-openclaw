export class GridPlacementError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'GridPlacementError';
  }
}

interface SpriteInput {
  id: string;
  name: string;
  width: number;
  height: number;
}

export function calculateGridPositions(
  sprites: SpriteInput[],
  atlasWidth: number,
  tileWidth: number,
  gap: number
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  
  if (sprites.length === 0) return positions;

  let currentX = 0;
  let currentY = 0;
  let spritesInRow = 0;

  for (const sprite of sprites) {
    // Check if sprite fits in atlas width
    if (sprite.width > atlasWidth) {
      throw new GridPlacementError(
        `Sprite "${sprite.name}" (width: ${sprite.width}) does not fit in atlas width (${atlasWidth})`
      );
    }

    // Check if we need to wrap to next row
    if (currentX + sprite.width > atlasWidth) {
      currentX = 0;
      currentY += tileWidth + gap;
      spritesInRow = 0;
    }

    positions.set(sprite.id, { x: currentX, y: currentY });
    currentX += sprite.width + gap;
    spritesInRow++;
  }

  return positions;
}
