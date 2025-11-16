import React, { useState } from "react";
import "./QuestionnaireModal.css";
import { useNavigate } from "react-router-dom";

interface QuestionnaireModalProps {
  onClose: () => void;
  onBack: () => void;
  initialFiles: File[];
}

const QuestionnaireModal: React.FC<QuestionnaireModalProps> = ({ onClose, onBack, initialFiles }) => {
  const navigate = useNavigate();

  const [numQuestions, setNumQuestions] = useState(5);
  const [timeMinutes, setTimeMinutes] = useState(10);
  const [instructions, setInstructions] = useState("");

  const MAX_QUESTIONS = 15;
  const MAX_TIME = 120;
  const MAX_INSTRUCTIONS = 80;

  const isFormValid = instructions.trim().length > 0;

  const handleCreate = () => {
    if (!isFormValid) return; 

    navigate("/questions", {
      state: { numQuestions, timeMinutes, instructions, initialFiles },
    });
  };

  return (
    <div className="files-modal-2">
      <div className="close-button-container">
        <div className="title-modal">Configuração de Questionário</div>
        <button className="button-close" onClick={onClose}>
          <img src="/close.svg" alt="fechar" />
        </button>
      </div>

      <div className="subtitle-modal">
        Configure o número de questões, tempo máximo e o tópico do simulado.
      </div>

      <div className="config-container">

        <div className="config-row">
          <label>Número de Questões</label>
          <p className="max-limit-info">Máximo: {MAX_QUESTIONS} questões</p>
          <div className="slider-container">
            <input
              type="range"
              min="1"
              max={MAX_QUESTIONS}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="slider"
            />
            <span className="slider-value">{numQuestions}</span>
          </div>
        </div>

        <div className="config-row">
          <label>Tempo Limite (minutos)</label>
          <p className="max-limit-info">Máximo: {MAX_TIME} minutos</p>
          <div className="slider-container">
            <input
              type="range"
              min="1"
              max={MAX_TIME}
              value={timeMinutes}
              onChange={(e) => setTimeMinutes(Number(e.target.value))}
              className="slider"
            />
            <span className="slider-value">{timeMinutes}</span>
          </div>
        </div>

        <div className="config-row">
          <label>Matéria / Tópico</label>

          <input
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Ex: Inteligência Artificial, História do Brasil, Matemática..."
            className="topic-area"
            maxLength={MAX_INSTRUCTIONS}
          />

          <div className="char-count">
            {instructions.length}/{MAX_INSTRUCTIONS} caracteres
          </div>

         </div>
      </div>

      <div className="footer-modal" style={{ marginTop: "2rem" }}>
        <button className="cancel-button" onClick={onBack}>Voltar</button>

        <button
          className="attach-button"
          onClick={handleCreate}
          disabled={!isFormValid}
          style={{
            opacity: isFormValid ? 1 : 0.5,
            cursor: isFormValid ? "pointer" : "not-allowed",
          }}
        >
          Gerar {numQuestions} questões
        </button>
      </div>
    </div>
  );
};

export default QuestionnaireModal;
