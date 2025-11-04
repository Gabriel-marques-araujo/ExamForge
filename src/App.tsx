import { useState } from 'react'
import './App.css'
import NavBar from './Components/NavBar/NavBar'
import FilesModal from './Components/FilesModal/FilesModal'

function App() {
  const [isFilesModalOpen, setIsFilesModalOpen] = useState(false)

  return (
    <>
      <NavBar className={isFilesModalOpen ? 'blur' : ''}/>
      <main className={isFilesModalOpen ? 'blur' : ''}>
        <div className="container">
          <div className="text-area">
            <div className='title'>Crie Simulados com</div>
            <div className='title2'>Inteligência Artificial</div>
            <div className='subtitle'>Crie questões e simulados do seu jeito! 
              Nossa plataforma usa os seus materiais para gerar milhares de perguntas 
              personalizadas em segundos — garantindo um estudo focado, rápido e 
              do seu jeito. Estudar nunca foi tão fácil!</div>
          </div>
          <div className="image-area">
            <img
                src="/image.svg"
                alt="imagem com livros e questionários saindo deles"
                className="books-image"
                />
          </div>
        </div>
        <button className="start-button" onClick={() => setIsFilesModalOpen(true)}>
          CRIE SEU SIMULADO AGORA!
        </button>
      </main>
      {isFilesModalOpen && <FilesModal onClose={() => setIsFilesModalOpen(false)} />}
    </>
  )
}

export default App
