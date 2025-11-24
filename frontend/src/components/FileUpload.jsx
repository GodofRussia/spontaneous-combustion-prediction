import {useCallback, useState} from 'react';
import {useDropzone} from 'react-dropzone';
import {validateCSVFile, formatFileSize} from '../services/dataProcessor';

const FileUpload = ({ label, onUpload, required = false, uploadedFile, multiple = false }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (multiple) {
      // Handle multiple files
      for (const file of acceptedFiles) {
        const validation = validateCSVFile(file);
        if (!validation.valid) {
          setError(`${file.name}: ${validation.error}`);
          continue;
        }

        setError(null);
        setUploading(true);

        try {
          await onUpload(file);
        } catch (err) {
          setError(err.message || 'Ошибка загрузки файла');
        } finally {
          setUploading(false);
        }
      }
    } else {
      // Handle single file
      const file = acceptedFiles[0];
      if (!file) return;

      const validation = validateCSVFile(file);
      if (!validation.valid) {
        setError(validation.error);
        return;
      }

      setError(null);
      setUploading(true);

      try {
        await onUpload(file);
      } catch (err) {
        setError(err.message || 'Ошибка загрузки файла');
      } finally {
        setUploading(false);
      }
    }
  }, [onUpload, multiple]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'] },
    multiple: multiple,
    disabled: uploading,
  });

  return (
    <div className="file-upload">
      {label && (
        <label className="file-upload-label">
          {label}
          {required && <span className="required">*</span>}
        </label>
      )}

      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''} ${uploadedFile ? 'uploaded' : ''}`}
      >
        <input {...getInputProps()} />
        {uploading ? (
          <div className="upload-status">
            <div className="spinner"></div>
            <p>Загрузка...</p>
          </div>
        ) : uploadedFile ? (
          <div className="upload-success">
            <span className="success-icon">✓</span>
            <p className="file-name">{uploadedFile.name}</p>
            <p className="file-size">{formatFileSize(uploadedFile.size)}</p>
            <p className="upload-hint">Нажмите или перетащите для замены</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <span className="upload-icon">📁</span>
            <p>Перетащите CSV {multiple ? 'файлы' : 'файл'} сюда или нажмите для выбора</p>
            <p className="upload-hint">Максимальный размер: 50 МБ{multiple ? ' на файл' : ''}</p>
          </div>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}
    </div>
  );
};

export default FileUpload;