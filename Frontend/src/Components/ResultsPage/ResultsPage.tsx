import React from "react";
import { useLocation, useNavigate } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./ResultsPage.css";
import { jsPDF } from "jspdf";

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    score = 10.0,
    totalQuestions = 20,
    correctAnswers = 13,
    wrongAnswers = 7,
  } = location.state || {};

  const percentage = ((correctAnswers / totalQuestions) * 100).toFixed(0);

  const handleBackToStart = () => navigate("/");
  const handleReviewAnswers = () => {
    navigate("/review", {
      state: {
        questions: location.state?.questions,
        userAnswers: location.state?.userAnswers,
      },
    });
  };

  const handleRetake = () => navigate("/questions");

  const handleExportPDF = async () => {
    try {
      const { jsPDF } = await import("jspdf");
      const elemento = document.getElementById("conteudoParaPDF");

      if (!elemento) {
        alert("Erro: elemento 'conteudoParaPDF' não encontrado!");
        return;
      }

      const doc = new jsPDF({
        orientation: "p",
        unit: "mm",
        format: "a4",
      });

      await doc.html(elemento, {
        callback: (doc) => {
          doc.save("resultado.pdf");
        },
        x: 10,
        y: 10,
        width: 190,
        windowWidth: 900,
      });
    } catch (error) {
      console.error("Erro ao exportar PDF:", error);
      alert("Ocorreu um erro ao gerar o PDF.");
    }
  };

  return (
    <>
      <NavBar />

      <div className="results-wrapper" id="conteudoParaPDF">
        <div className="results-main">
          {/* === Seção da nota === */}
          <div className="score-section">
            <div className="score-background">
              <div className="decor-circle circle2"></div>
              <div className="decor-circle circle1"></div>
              <div className="score-circle">{score.toFixed(1)}</div>
            </div>
            <h2 className="score-label">Sua Nota</h2>
          </div>

          {/* === Seção das estatísticas === */}
          <div className="stats-section">
            <div className="stat-card">
              <span className="dot red-dot"></span>
              <div>
                <h3>{totalQuestions}</h3>
                <p>Questões</p>
              </div>
            </div>

            <div className="stat-card">
              <span className="dot green-dot"></span>
              <div>
                <h3>{correctAnswers}</h3>
                <p>Corretas</p>
              </div>
            </div>

            <div className="stat-card">
              <span className="dot red-dot"></span>
              <div>
                <h3>{wrongAnswers}</h3>
                <p>Erradas</p>
              </div>
            </div>
          </div>

          {/* === Botões === */}
          <div className="results-actions">
            <button className="action-button" onClick={handleReviewAnswers}>
              Revisar Respostas
            </button>
            <button className="action-button" onClick={handleRetake}>
              Refazer Simulado
            </button>
            <button className="action-button" onClick={handleExportPDF}>
              Exportar PDF
            </button>
            <button className="restart-button" onClick={handleBackToStart}>
              Voltar ao Início
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ResultsPage;
