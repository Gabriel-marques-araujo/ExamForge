import React, { useState, useEffect } from 'react';
import './App.css';
import NavBar from './Components/NavBar/NavBar';
import FilesModal from './Components/FilesModal/FilesModal';
import QuestionnaireModal from './Components/QuestionnaireModal/QuestionnaireModal';

function App() {
  const [isFilesModalOpen, setIsFilesModalOpen] = useState(false);
  const [isQuestionnaireModalOpen, setIsQuestionnaireModalOpen] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem("theme") === "dark";
  });
  
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
  }, [darkMode]);

  return (
    <>
      <NavBar className={isFilesModalOpen || isQuestionnaireModalOpen ? 'blur' : ''} 
      onThemeChange={setDarkMode}/>
      <main className={isFilesModalOpen || isQuestionnaireModalOpen ? 'blur' : ''}>
        <div className="container">
          <div className="text-area">
            <div className='title'>Crie Simulados com</div>
            <div className='title2'>Inteligência Artificial</div>
            <div className='subtitle'>
              Crie questões e simulados do seu jeito! Nossa plataforma usa os seus materiais para gerar milhares de perguntas 
              personalizadas em segundos — garantindo um estudo focado, rápido e do seu jeito. Estudar nunca foi tão fácil!
            </div>
          </div>
          <div className="image-area">
            <img
              src={darkMode ? "/logo2-dark.svg" : "/logo2.svg"}
              alt="aluna com computador pensando em questionários"
              className="books-image"

            />
          </div>

        </div>


        <button className="start-button" onClick={() => setIsFilesModalOpen(true)}>
          CRIE SEU SIMULADO AGORA!
        </button>
      </main>

      {/* Modal de arquivos */}
      {isFilesModalOpen && (
        <FilesModal
          onClose={() => setIsFilesModalOpen(false)}
          onNext={(files: File[]) => {
            setUploadedFiles(files);
            setIsFilesModalOpen(false);
            setIsQuestionnaireModalOpen(true);
          }}
        />
      )}

      {isQuestionnaireModalOpen && (
        <QuestionnaireModal
          initialFiles={uploadedFiles}
          onClose={() => setIsQuestionnaireModalOpen(false)}
          onBack={() => {
            setIsQuestionnaireModalOpen(false);
            setIsFilesModalOpen(true);
          }}
        />
      )}
    </>
  );
}

export default App;