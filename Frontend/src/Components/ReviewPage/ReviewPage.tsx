import React from "react";
import { useLocation } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./ReviewPage.css";

interface Question {
  id: number;
  enunciado: string;
  alternativas: string[];
  correctAnswer: string;
  explicacao: string;
}

interface ReviewState {
  questions: Question[];
  userAnswers: string[];
  timeSpentInSeconds?: number;
  totalQuestions?: number;
  correctAnswers?: number;
}

const ReviewPage: React.FC = () => {
  const location = useLocation();
  const { 
    questions = [], 
    userAnswers = [],
    timeSpentInSeconds = 0,
    totalQuestions = 0,
    correctAnswers = 0
  } = (location.state as ReviewState) || {};

  const timeMinutes = Math.floor(timeSpentInSeconds / 60);
  const timeSeconds = timeSpentInSeconds % 60;
  const wrongAnswers = totalQuestions - correctAnswers;

  if (!questions.length) {
    return (
      <>
        <NavBar />
        <div className="review-container review-empty">
          <p>Nenhum dado encontrado para revisão.</p>
        </div>
      </>
    );
  }

  return (
    <>
      <NavBar />
      <div className="review-wrapper">
        <div className="review-stats-header">
          <div className="stat-item">
            <span className="stat-label">Total de Questões</span>
            <span className="stat-value total-q">{totalQuestions}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Corretas</span>
            <span className="stat-value correct-q">{correctAnswers}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Erradas</span>
            <span className="stat-value wrong-q">{wrongAnswers}</span>
          </div>
          <div className="stat-item time-stat">
            <span className="stat-label">Tempo Gasto</span>
            <span className="stat-value time-q">
              {timeMinutes.toString().padStart(2, '0')}:{timeSeconds.toString().padStart(2, '0')}
            </span>
          </div>
        </div>
        
        <div className="review-container">
          {questions.map((q: Question, i: number) => {
            const userAnswer = userAnswers[i];
            const isCorrect = userAnswer === q.correctAnswer;

            return (
              <div key={q.id} className="question-card-review">
                <h3 className="card-title">Questão {i + 1}</h3>
                <p className="enunciado">{q.enunciado}</p>

                <div className="alternativas">
                  {q.alternativas.map((alt, idx) => {
                    const isUserChoice = alt === userAnswer;
                    const isRight = alt === q.correctAnswer;
                    const className = isRight
                      ? "alt-correct"
                      : isUserChoice && !isRight
                      ? "alt-wrong"
                      : "alt-neutral";

                    return (
                      <div key={idx} className={className}>
                        {alt}
                        {isUserChoice && <span className="marker">{isRight ? 'Sua Resposta (Correta)' : 'Sua Resposta (Errada)'}</span>}
                        {isRight && !isUserChoice && <span className="marker">Resposta Correta</span>}
                      </div>
                    );
                  })}
                </div>

                <div className="explicacao">
                  <strong>Explicação:</strong> {q.explicacao}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </>
  );
};

export default ReviewPage;