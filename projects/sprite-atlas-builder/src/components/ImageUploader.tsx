import { useCallback, useState } from 'react';
import { createSprite } from '../domain/Sprite';
import type { Sprite } from '../domain/Sprite';
import './ImageUploader.css';

interface Props {
  onImagesLoaded: (sprites: Sprite[]) => void;
}

export function ImageUploader({ onImagesLoaded }: Props) {
  const [isDragging, setIsDragging] = useState(false);

  const processFiles = useCallback((files: FileList) => {
    const imageFiles = Array.from(files).filter(file =>
      file.type.startsWith('image/')
    );

    const sprites: Sprite[] = [];

    imageFiles.forEach((file, index) => {
      const img = new Image();
      img.onload = () => {
        const sprite = createSprite({
          id: `sprite-${Date.now()}-${index}`,
          name: file.name,
          width: img.width,
          height: img.height,
          sourceUrl: URL.createObjectURL(file),
          metadata: {
            format: file.type.includes('png') ? 'PNG' : file.type.includes('jpeg') ? 'JPEG' : 'WEBP',
            originalSize: file.size,
          },
        });
        sprites.push(sprite);

        if (sprites.length === imageFiles.length) {
          onImagesLoaded(sprites);
        }
      };
      img.src = URL.createObjectURL(file);
    });
  }, [onImagesLoaded]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  }, [processFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(e.target.files);
    }
  }, [processFiles]);

  return (
    <div
      className={`image-uploader ${isDragging ? 'dragging' : ''}`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <div className="upload-content">
        <span className="upload-icon">📁</span>
        <p>Drop images here</p>
        <p className="upload-hint">or</p>
        <label className="upload-button">
          Browse Files
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={handleFileInput}
            style={{ display: 'none' }}
          />
        </label>
        <p className="upload-formats">PNG, JPG, WEBP</p>
      </div>
    </div>
  );
}
