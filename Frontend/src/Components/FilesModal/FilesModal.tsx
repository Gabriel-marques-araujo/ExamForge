import React, { useState } from "react";
import axios from "axios";
import "./FilesModal.css";

interface FilesModalProps {
  onClose: () => void;
  onNext: (files: File[]) => void;
}

interface UploadedFile {
  file: File;
  progress: number;
  error?: string;
}

const FilesModal: React.FC<FilesModalProps> = ({ onClose, onNext }) => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>("");
  const [isDragging, setIsDragging] = useState(false);

  const processFiles = (fileList: FileList) => {
    const newFiles: UploadedFile[] = [];

    const validTypes = [
      "application/pdf",
      "text/plain",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ];

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];

      if (!validTypes.includes(file.type)) {
        setErrorMessage(`Arquivo "${file.name}" não suportado`);
        continue;
      }

      if (file.size > 25 * 1024 * 1024) {
        setErrorMessage(`Arquivo "${file.name}" excede 25MB`);
        continue;
      }

      newFiles.push({ file, progress: 0 });
    }

    if (newFiles.length === 0) return;

    setFiles(prev => [...prev, ...newFiles]);

    newFiles.forEach(f => {
      const interval = setInterval(() => {
        setFiles(prevFiles => {
          const updatedFiles = [...prevFiles];
          const index = updatedFiles.findIndex(p => p.file.name === f.file.name);

          if (index !== -1) {
            if (updatedFiles[index].progress >= 100) {
              updatedFiles[index].progress = 100;
              clearInterval(interval);
            } else {
              updatedFiles[index].progress += 5;
            }
          }

          return updatedFiles;
        });
      }, 100);
    });
    newFiles.forEach(async f => {
      const formData = new FormData();
      formData.append("file", f.file);

      try {
        await axios.post("http://localhost:8000/base/upload/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        console.log(`Upload concluído para ${f.file.name}`);

        await axios.post("http://localhost:8000/base/create/");
        console.log(`Vetorização iniciada para ${f.file.name}`);
      } catch (error) {
        console.error("Erro ao enviar arquivo:", error);
        setErrorMessage(`Erro ao enviar "${f.file.name}"`);
      }
    });

    setTimeout(() => setErrorMessage(""), 3000);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return;
    processFiles(event.target.files);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files.length > 0) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDragEnter = () => setIsDragging(true);
  const handleDragLeave = () => setIsDragging(false);

  const handleRemoveFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleNextClick = () => {
    const fileObjects = files
      .filter(f => f.progress === 100)
      .map(f => f.file);

    if (fileObjects.length > 0) {
      onNext(fileObjects);
    }
  };

  return (
    <div className="files-modal">
      <div className="close-button-container">
        <div className="title-modal">Carregar e anexar arquivos</div>
        <button className="button-close" onClick={onClose}>
          <img src="/close.svg" alt="fechar" className="close-button" />
        </button>
      </div>

      <div className="subtitle-modal">
        Carregue e anexe arquivos a este projeto.
      </div>

      <div
        className={`upload-area ${isDragging ? "dragging" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
      >
        <label htmlFor="file-input">
          <img src="/upload-icon.svg" alt="ícone de upload" className="upload-icon" />
          <div className="upload-text">
            <span className="browse-link">Clique para carregar</span> ou arraste e solte
          </div>
          <div className="file-types-text">PDF, TXT ou DOCX (max. 25MB)</div>
        </label>

        <input
          id="file-input"
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={handleFileChange}
        />
      </div>

      {errorMessage && (
        <div style={{ color: "#E64756", marginTop: "0.5rem" }}>
          {errorMessage}
        </div>
      )}
      {files.length > 0 && (
        <div
          className="uploaded-files-container"
          style={{ overflowY: files.length > 3 ? "scroll" : "auto" }}
        >
          {files.map((f, index) => (
            <div key={index} className="uploaded-file">
              <div className="file-row">
                <div className="file-icon">
                  {f.progress < 100 ? (
                    <img src="/file-upload-icon2.svg" alt="Arquivo" />
                  ) : (
                    <img src="/file-upload-icon.svg" alt="Arquivo" />
                  )}
                </div>

                <div className="file-info">
                  <span className="file-name">{f.file.name}</span>
                  <span className="file-size">{(f.file.size / 1024).toFixed(1)} KB</span>
                </div>

                {f.progress < 100 ? (
                  <button className="remove-file" onClick={() => handleRemoveFile(index)}>
                    <img src="/trash.svg" alt="Cancelar upload" />
                  </button>
                ) : (
                  <img src="/check.svg" alt="Upload concluído" className="check-icon" />
                )}
              </div>

              {f.progress > 0 && (
                <div className="progress-bar-container">
                  <div className="progress-bar-full">
                    <div
                      className="progress-fill-full"
                      style={{ width: `${f.progress}%` }}
                    ></div>
                  </div>
                  <span className="progress-percent-full">{f.progress}%</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      <div className="footer-modal">
        <button className="cancel-button" onClick={onClose}>Cancelar</button>
        <button
          className="attach-button"
          onClick={handleNextClick}
          disabled={files.length === 0 || files.some(f => f.progress < 100)}
          style={{
            cursor: files.length === 0 || files.some(f => f.progress < 100) ? "not-allowed" : "pointer",
            opacity: files.length === 0 || files.some(f => f.progress < 100) ? 0.5 : 1
          }}
        >
          Próximo
        </button>
      </div>
    </div>
  );
};

export default FilesModal;
