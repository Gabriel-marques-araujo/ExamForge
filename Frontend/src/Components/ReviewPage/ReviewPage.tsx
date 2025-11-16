import React, { useRef } from "react";
import { useLocation } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./ReviewPage.css";
import { jsPDF } from "jspdf";
import { CheckCircle, XCircle } from "lucide-react";

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
  instructions?: string;
}

const ReviewPage: React.FC = () => {
  const location = useLocation();
  const {
    questions = [],
    userAnswers = [],
    timeSpentInSeconds = 0,
    totalQuestions = 0,
    correctAnswers = 0,
    instructions = "Geral",
  } = (location.state as ReviewState) || {};

  const reviewRef = useRef<HTMLDivElement>(null);

  const timeMinutes = Math.floor(timeSpentInSeconds / 60);
  const timeSeconds = timeSpentInSeconds % 60;
  const wrongAnswers = totalQuestions - correctAnswers;

  const handleExportPDF = () => {
    if (!reviewRef.current) return;
    const doc = new jsPDF("p", "pt", "a4");
    doc.html(reviewRef.current, {
      callback: (doc) => doc.save("revisao.pdf"),
      x: 20,
      y: 20,
      width: 560,
      windowWidth: reviewRef.current.scrollWidth,
    });
  };

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
      <div className="review-wrapper" ref={reviewRef}>
        {/* === Estatísticas === */}
        <div className="review-stats-header">
          <div className="stat-item">
            <span className="stat-label">Tema:</span>
            <span className="stat-value">{instructions}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Total de Questões:</span>
            <span className="stat-value">{totalQuestions}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Corretas:</span>
            <span className="stat-value correct-q">{correctAnswers}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Erradas:</span>
            <span className="stat-value wrong-q">{wrongAnswers}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Tempo Gasto:</span>
            <span className="stat-value">
              {timeMinutes.toString().padStart(2, "0")}:
              {timeSeconds.toString().padStart(2, "0")}
            </span>
          </div>
        </div>

        {/* === Questões === */}
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
                      <span className="alt-text">{alt}</span>
                      {isRight && <CheckCircle className="icon-correct" />}
                      {isUserChoice && !isRight && <XCircle className="icon-wrong" />}
                      {isUserChoice && (
                        <span className="marker">
                          {isRight ? "Sua Resposta (Correta)" : "Sua Resposta (Errada)"}
                        </span>
                      )}
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

        <div className="export-button-container">
          <button className="export-pdf-button" onClick={handleExportPDF}>
            Exportar PDF
          </button>
        </div>
      </div>
    </>
  );
};

export default ReviewPage;
