export const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
export const MAX_BATCH_SIZE = 50 * 1024 * 1024; // 50MB
export const MIN_ATLAS_DIMENSION = 16;
export const MAX_ATLAS_DIMENSION = 4096;

export interface AtlasConfigInput {
  name: string;
  width: number;
  height: number;
  exportMode: 'PNG' | 'JSON' | 'ZIP';
  autoPack: boolean;
  gap: number;
  rotation: boolean;
}

export function validateAtlasConfig(config: AtlasConfigInput): void {
  if (config.width < MIN_ATLAS_DIMENSION || config.width > MAX_ATLAS_DIMENSION) {
    throw new Error(`Atlas width must be between ${MIN_ATLAS_DIMENSION} and ${MAX_ATLAS_DIMENSION}`);
  }
  if (config.height < MIN_ATLAS_DIMENSION || config.height > MAX_ATLAS_DIMENSION) {
    throw new Error(`Atlas height must be between ${MIN_ATLAS_DIMENSION} and ${MAX_ATLAS_DIMENSION}`);
  }
  if (config.gap < 0) {
    throw new Error('Gap must be non-negative');
  }
}

export function validateFileSize(fileSize: number): void {
  if (fileSize > MAX_FILE_SIZE) {
    throw new Error(`File size exceeds maximum of ${MAX_FILE_SIZE} bytes`);
  }
}

export function validateBatchSize(totalSize: number): void {
  if (totalSize > MAX_BATCH_SIZE) {
    throw new Error(`Batch size exceeds maximum of ${MAX_BATCH_SIZE} bytes`);
  }
}
