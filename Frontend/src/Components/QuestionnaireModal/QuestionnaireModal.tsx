import React, { useState } from "react";
import "./QuestionnaireModal.css";
import { useNavigate } from "react-router-dom";
import axios from "axios";

interface QuestionnaireModalProps {
  onClose: () => void;
  onBack: () => void;
  initialFiles: File[];
}

const QuestionnaireModal: React.FC<QuestionnaireModalProps> = ({ onClose, onBack, initialFiles }) => {
  const navigate = useNavigate();

  const [numQuestions, setNumQuestions] = useState(5);
  const [timeMinutes, setTimeMinutes] = useState(10);
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);

  const MAX_QUESTIONS = 15;
  const MAX_TIME = 120;
  const MAX_INSTRUCTIONS = 80;

  const isFormValid = topic.trim().length > 0;

  const incrementQuestions = () => setNumQuestions(prev => Math.min(prev + 1, MAX_QUESTIONS));
  const decrementQuestions = () => setNumQuestions(prev => Math.max(prev - 1, 1));

  const incrementTime = () => setTimeMinutes(prev => Math.min(prev + 1, MAX_TIME));
  const decrementTime = () => setTimeMinutes(prev => Math.max(prev - 1, 1));


  const handleCreate = async () => {
    setLoading(true);
  const payload = {
    topic: topic,
    qnt_questoes: numQuestions,
  };

  try {
    const response = await axios.post("http://localhost:8000/rag/generate_mcq/", payload);
    console.log("MCQs gerados:", response.data);

    navigate("/questions", {
      state: {
        numQuestions,
        timeMinutes,
        topic,
        initialFiles,
        generatedQuestions: response.data,
      },
    });
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error("Erro ao gerar questões:", error);
      alert(`Erro ao gerar questões: ${error.response?.data?.error || "Falha no servidor"}`);
    } else {
      console.error("Não foi possível conectar ao backend.");
      alert("Não foi possível conectar ao backend.");
    }
  } finally{
    setLoading(false);
  }
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
          <label>Matéria / Tópico</label>

          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Ex: Inteligência Artificial, História do Brasil, Matemática..."
            className="topic-area"
            maxLength={MAX_INSTRUCTIONS}
          />
          <div className="char-counter"
            style={{
              textAlign: "right",
              fontSize: "1rem",
              
              marginTop: "0.25rem",
              fontFamily: "inter, sans-serif",
            }}
          >
           {topic.length}/{MAX_INSTRUCTIONS} caracteres
           </div>
         </div>
      </div>

      <div className="footer-modal" style={{ marginTop: "2rem" }}>
        <button className="cancel-button" onClick={onBack}>Voltar</button>

        <button
          className="attach-button"
          onClick={handleCreate}
          disabled={!isFormValid || loading}
          style={{
            opacity: (isFormValid && !loading) ? 1 : 0.5,
            cursor: (isFormValid && !loading) ? "pointer" : "not-allowed",
          }}
        >
          {loading ? "Gerando..." : `Gerar ${numQuestions} questões`}
        </button>
      </div>
    </div>
  );
};

export default QuestionnaireModal;