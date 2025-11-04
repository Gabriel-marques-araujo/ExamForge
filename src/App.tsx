import { useState } from 'react'
import './App.css'
import NavBar from './NavBar/NavBar'

function App() {

  return (
    <>
      <NavBar />
      <main>
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
        <button className="start-button">
          CRIE SEU SIMULADO AGORA!
        </button>
      </main>
    </>
  )
}

export default App
