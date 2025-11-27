import { useLocation, useNavigate } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./ResultsPage.css";
import axios from "axios";


const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    score = 10.0,
    totalQuestions = 10,
    correctAnswers = 10,
    wrongAnswers = 0,
    questions = [],
    timeMinutes,
    topic,
    initialFiles,
  } = location.state || {};

  const handleBackToStart = () => navigate("/");

  const handleRetake = () => {
    navigate("/questions", {
      state: {
        timeMinutes,
        topic,
        initialFiles,


        generatedQuestions: questions.map((q: { rawData: any; }) => q.rawData || q),
      },
    });
  };

  
const handleExportPDF = async () => {
  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/rag/generate_PDF/",
      {},
      { responseType: "blob" } 
    );

    // Cria um blob com o PDF retornado
    const pdfBlob = new Blob([response.data], { type: "application/pdf" });

    // Cria um link temporário para download
    const link = document.createElement("a");
    link.href = URL.createObjectURL(pdfBlob);
    link.download = "exame.pdf"; 
    document.body.appendChild(link);
    link.click();
    link.remove(); 

    alert("PDF gerado e baixado com sucesso!");
  } catch (error) {
    console.error("Erro ao gerar PDF:", error);
    alert("Erro ao gerar PDF: " + error);
  }
};

return (
  <>
    <NavBar />

    <div className="results-wrapper" id="conteudoParaPDF">
      <div className="results-main">
        <div className="results-content">
          <div className="big-score-box">
            <h1 className="big-score-title">SUA NOTA</h1>

            <div className="score-display">
              <span>{score.toFixed(1)}</span>
            </div>
          </div>
          <div className="stats-box">
            <div className="stats-section">
              <div className="stat-card">
                <span className="dot yellow-dot"></span>
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
          </div>

          <div className="feedback-area">
            <h2>Avaliação de Desempenho</h2>
            <p className="feedback-text">
              Com base nas suas respostas, percebi que você precisa reforçar seus estudos em <strong>Programação Orientada a Objetos (POO).</strong><br />
              Você demonstrou dificuldade em conceitos como <strong>abstração, encapsulamento e herança</strong>, especialmente ao indentificar quando cada um deve ser aplicado.<br />
              <strong>Sugestão:</strong> revise exemplos práticos de classes e objetos, pratique a criação de modelos simples e tente resolver exercícios que envolvam relacionar classes entre si. Isso vai ajudar a fixar melhor esses conceitos.
            </p>
          </div>

          <div className="results-actions">

            <button className="result-button" onClick={handleRetake}>
              Refazer Simulado
            </button>

            <button className="result-button" onClick={handleExportPDF}>
              Exportar PDF
            </button>

            <button className="result-button" onClick={handleBackToStart}>
              Voltar ao Início
            </button>
          </div>

        </div>
      </div>
    </div>
  </>
);
};

export default ResultsPage;