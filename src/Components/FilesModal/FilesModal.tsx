import "./FilesModal.css";
import React from "react";



interface FilesModalProps {
    onClose: () => void;
}

const FilesModal: React.FC<FilesModalProps> = ({ onClose }) => {
    return (
        <div className="files-modal">
                <div className="close-button-container">
                        <div className="title-modal">Carregar e anexar arquivos</div>
                        <button className="button-close" onClick={onClose}>
                        <img 
                                src="/close.svg"
                                alt="fechar"
                                className="close-button"
                        />
                        </button>
                </div>
                <div className="subtitle-modal">Carregue e anexe arquivos a este projeto.</div>
                <div className="upload-area">
                    <img
                       src="/upload-icon.svg"
                        alt="ícone de upload"
                       className="upload-icon"
                    />
                    <div className="upload-text"><span className="browse-link">Clique para carregar</span> ou arraste e solte</div>
                    <div className="file-types-text">PDF, TXT ou DOCX (max. 25MB)</div>
                </div>
                <div className="footer-modal">
                    <button className="cancel-button" onClick={onClose}>Cancelar</button>
                    <button className="attach-button" onClick={onClose}>Próximo</button>
                </div>
        </div>
    );
};

export default FilesModal;