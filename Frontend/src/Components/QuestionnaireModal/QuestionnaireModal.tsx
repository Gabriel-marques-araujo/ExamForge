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

  const [numQuestions, setNumQuestions] = useState(1);
  const [timeMinutes, setTimeMinutes] = useState(10);
  const [instructions, setInstructions] = useState("");

  const MAX_QUESTIONS = 15;
  const MAX_TIME = 120;
  const MAX_INSTRUCTIONS = 240;

  const incrementQuestions = () => setNumQuestions(prev => Math.min(prev + 1, MAX_QUESTIONS));
  const decrementQuestions = () => setNumQuestions(prev => Math.max(prev - 1, 1));

  const incrementTime = () => setTimeMinutes(prev => Math.min(prev + 1, MAX_TIME));
  const decrementTime = () => setTimeMinutes(prev => Math.max(prev - 1, 1));

  const handleCreate = () => {
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
        Configure o número de questões, tempo máximo e instruções para o simulado.
      </div>

      <div className="config-container">
        <div className="config-row">
          <label>Número de Questões:</label>
          <div className="input-with-buttons">
            <button className="circle-btn" onClick={decrementQuestions}>-</button>
            <input
              type="number"
              value={numQuestions}
              onChange={(e) => {
                let value = Number(e.target.value);
                if (value < 1) value = 1;
                if (value > MAX_QUESTIONS) value = MAX_QUESTIONS;
                setNumQuestions(value);
              }}
              min="1"
              max={MAX_QUESTIONS}
            />
            <button className="circle-btn" onClick={incrementQuestions}>+</button>
          </div>
          <div className="max-info">Máximo de {MAX_QUESTIONS} questões por simulado</div>
        </div>

        <div className="config-row">
          <label>Tempo Limite (minutos):</label>
          <div className="input-with-buttons">
            <button className="circle-btn" onClick={decrementTime}>-</button>
            <input
              type="number"
              value={timeMinutes}
              onChange={(e) => {
                let value = Number(e.target.value);
                if (value < 1) value = 1;
                if (value > MAX_TIME) value = MAX_TIME;
                setTimeMinutes(value);
              }}
              min="1"
              max={MAX_TIME}
            />
            <button className="circle-btn" onClick={incrementTime}>+</button>
          </div>
          <div className="max-info">Máximo de {MAX_TIME} minutos por simulado</div>
        </div>

        <div className="config-row">
          <label>Instruções para as questões:</label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Digite como deseja que as questões sejam elaboradas..."
            rows={6}
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: "12px",
              border: "1px solid #E9EAEB",
              fontFamily: "inter, sans-serif",
              fontSize: "1rem",
              marginTop: "0.5rem",
              resize: "none",
              boxSizing: "border-box",
            }}
            maxLength={MAX_INSTRUCTIONS}
          />
          <div
            style={{
              textAlign: "right",
              fontSize: "0.75rem",
              color: "#535862",
              marginTop: "0.25rem",
              fontFamily: "inter, sans-serif",
            }}
          >
            {instructions.length}/{MAX_INSTRUCTIONS} caracteres
          </div>
        </div>
      </div>

      <div className="footer-modal" style={{ marginTop: "2rem" }}>
        <button className="cancel-button" onClick={onBack}>Voltar</button>
        <button className="attach-button" onClick={handleCreate}>Criar</button>
      </div>
    </div>
  );
};

export default QuestionnaireModal;
