import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./QuestionPage.css";

interface Question {
  id: number;
  enunciado: string;
  alternativas: string[];
  correctAnswer: string;
  explicacao: string;
}

interface LocationState {
  timeMinutes: number;
  instructions?: string; 
  initialFiles?: File[];
}

const QuestionsPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as LocationState | undefined;
  const timeMinutes = state?.timeMinutes || 120;
  const topic = state?.instructions || "Geral";

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: string }>({});
  const [timeLeft, setTimeLeft] = useState(timeMinutes * 60);
  const [isTimeOver, setIsTimeOver] = useState(false);
  const [showWarning, setShowWarning] = useState(false);

  useEffect(() => {
    if (timeLeft <= 0) {
      setIsTimeOver(true);
      return;
    }
    const interval = setInterval(() => setTimeLeft((prev) => prev - 1), 1000);
    return () => clearInterval(interval);
  }, [timeLeft]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

const questions: Question[] = [
  {
    id: 1,
    enunciado: "O que é um caso de teste?",
    alternativas: [
      "A) Um defeito encontrado no sistema",
      "B) Uma funcionalidade a ser desenvolvida",
      "C) Um conjunto de condições para verificar um requisito",
      "D) Um relatório de execução de teste",
    ],
    correctAnswer: "C) Um conjunto de condições para verificar um requisito",
    explicacao: "Um caso de teste define condições necessárias para validar um requisito.",
  },
  {
    id: 2,
    enunciado: "O que é teste de regressão?",
    alternativas: [
      "A) Teste realizado apenas no início do projeto",
      "B) Teste para verificar se alterações causaram falhas",
      "C) Teste de performance em produção",
      "D) Teste exploratório",
    ],
    correctAnswer: "B) Teste para verificar se alterações causaram falhas",
    explicacao: "É executado após mudanças no sistema para garantir que nada foi quebrado.",
  },
];

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  const handleSelect = (questionId: number, option: string) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) setCurrentQuestionIndex((prev) => prev + 1);
    else handleSubmit();
  };

  const handleBack = () => {
    if (currentQuestionIndex > 0) setCurrentQuestionIndex((prev) => prev - 1);
  };

  const handleSubmit = () => {
    navigate("/resultado", {
      state: {
        score: 10.0,
        totalQuestions: questions.length,
        correctAnswers: 13,
        wrongAnswers: 7,
        questions: questions,         
        userAnswers: selectedAnswers, 
        topic, 
      },
    });
  };

  return (
    <>
      <NavBar />

      <div className="questions-container">
        <div className="question-card">
<div className="top-info-bar">
 <div className="topic-section">
  <span className="label">Tópico:</span>
  <span className="value">{topic}</span>
</div>


  <div className="timer-section">
    <span className="label">Tempo Restante:</span>
    <span className="value">{formatTime(timeLeft)}</span>
  </div>
</div>

          <div className="progress-bar">
            <div className="progress" style={{ width: `${progress}%` }} />
          </div>

          <div className="question-header-with-timer">

            <div className="question-header">
              <div className="question-number">{currentQuestion.id}</div>
              <p className="question-text">{currentQuestion.enunciado}</p>

              {showWarning && (
                <p className="warning-text">⚠️ Selecione uma alternativa para continuar.</p>
              )}
            </div>

          </div>

          <div className="options">
            {currentQuestion.alternativas.map((alt, idx) => (
              <label
                key={idx}
                className={`option-box ${
                  selectedAnswers[currentQuestion.id] === alt ? "selected" : ""
                }`}
                onClick={() => handleSelect(currentQuestion.id, alt)}
              >
                <input
                  type="radio"
                  name={`question-${currentQuestion.id}`}
                  value={alt}
                  checked={selectedAnswers[currentQuestion.id] === alt}
                  onChange={() => handleSelect(currentQuestion.id, alt)}
                  style={{ display: "none" }}
                />
                {alt}
              </label>
            ))}
          </div>
          <div className={`actions ${currentQuestionIndex === 0 ? "first-question" : ""}`}>
            {currentQuestionIndex > 0 && (
              <button className="back-button" onClick={handleBack}>
                Voltar
              </button>
            )}

            {currentQuestionIndex < questions.length - 1 ? (
              <button
                className="next-button"
                onClick={() => {
                  if (!selectedAnswers[currentQuestion.id]) {
                    setShowWarning(true);
                    return;
                  }
                  setShowWarning(false);
                  handleNext();
                }}
              >
                Próxima
              </button>
            ) : (
              <button
                className="submit-button"
                onClick={() => {
                  if (!selectedAnswers[currentQuestion.id]) {
                    setShowWarning(true);
                    return;
                  }
                  setShowWarning(false);
                  handleNext();
                }}
              >
                Finalizar Simulado
              </button>
            )}
          </div>

        </div>
      </div>

      {isTimeOver && (
        <div className="time-over-modal">
          <div className="time-over-content">
            <h2>O tempo acabou!</h2>
            <button className="submit-button" onClick={handleSubmit}>
              Finalizar Simulado
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default QuestionsPage;
