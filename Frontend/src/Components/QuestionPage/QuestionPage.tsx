import React, { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import NavBar from "../NavBar/NavBar";
import "./QuestionPage.css";
import axios from "axios";

interface Question {
  id: number;
  enunciado: string;
  alternativas: string[];
  rawData?: any;
  correctAnswer: string;
  explicacao: string;
}

interface LocationState {
  timeMinutes: number;
  topic?: string;
  initialFiles?: File[];
  generatedQuestions?: any;
}

const QuestionsPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const state = location.state as LocationState | undefined;
  const timeMinutes = state?.timeMinutes || 120;
  const topic = state?.topic || "Geral";
  const generatedQuestions = state?.generatedQuestions || [];

  const questions: Question[] = React.useMemo(() => {
    if (!generatedQuestions) return [];

    const raw = Array.isArray(generatedQuestions)
      ? generatedQuestions
      : Object.values(generatedQuestions);

    const validQuestions = raw.filter(
      (q: any) =>
        q &&
        (q.enunciado || q.question || q.text) &&
        (q.alternativas || q.options || q.choices)
    );

    return validQuestions.map((q: any, i: number) => ({
      id: q.id ?? i + 1,
      enunciado: q.enunciado || q.question || q.text || `Questão ${i + 1}`,
      alternativas: q.alternativas || q.options || q.choices || [],
      correctAnswer: q.correctAnswer || q.correct_answer || q.answer || "",
      explicacao: q.explicacao || q.explanation || q.details || "",
      rawData: q,
    }));
  }, [generatedQuestions]);

  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: string }>({});
  const [timeLeft, setTimeLeft] = useState(timeMinutes * 60);
  const [isTimeOver, setIsTimeOver] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [results, setResults] = useState<{ [key: number]: any }>({});

  if (questions.length === 0) {
    return (
      <div className="questions-container">
        <NavBar />
        <div className="no-questions">
          <h2>Nenhuma questão foi carregada 😕</h2>
          <button onClick={() => navigate(-1)} className="back-button">
            Voltar
          </button>
        </div>
      </div>
    );
  }

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

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;
  const feedback = results[currentQuestion.id];

  const handleSelect = (questionId: number, option: string) => {
    setSelectedAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const checkAnswer = async (question: Question, chosenOption: string) => {
    try {
      const response = await axios.post("http://localhost:8000/rag/check_answer/", {
        question_data: question.rawData,
        chosen_option: chosenOption,
      });
      return response.data;
    } catch (error) {
      console.error("Erro ao verificar resposta:", error);
      return null;
    }
  };

  const handleNext = async () => {
    const chosenOption = selectedAnswers[currentQuestion.id];

    if (!chosenOption) {
      setShowWarning(true);
      return;
    }

    setShowWarning(false);

    if (showFeedback) {
      setShowFeedback(false);
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex((prev) => prev + 1);
      } else {
        handleSubmit();
      }
      return;
    }

    const result = await checkAnswer(currentQuestion, chosenOption);
    if (result) {
      setResults((prev) => ({ ...prev, [currentQuestion.id]: result }));
    }

    setShowFeedback(true);
  };

  const handleBack = () => {
    if (currentQuestionIndex > 0) {
      setShowFeedback(false);
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const handleSubmit = () => {
    const correct = Object.values(results).filter((r) => r.is_correct).length;
    const totalQuestions = questions.length;

    const score = (correct / totalQuestions) * 10;
    const wrong = totalQuestions - correct;

    navigate("/resultado", {
      state: {
        score,
        totalQuestions,
        correctAnswers: correct,
        wrongAnswers: wrong,
        questions,
        userAnswers: selectedAnswers,
        timeMinutes,
        topic,
        initialFiles: state?.initialFiles || [],
        results,
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
              <span className="label"><img
              src="/clock.svg"
              alt="relógio"
              className="clock"
              /> Tempo Restante:</span>
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
              <button className="new-question-button">
                Nova Questão
              </button>
            </div>
          </div>
          {showWarning && (
            <p className="warning-text">⚠️ Selecione uma alternativa para continuar.</p>
          )}
            

          <div className="options">
            {currentQuestion.alternativas.map((alt: any, idx: number) => {
              const text = typeof alt === "string" ? alt : alt.option;
              return (
                <label
                  key={idx}
                  className={`option-box 
                    ${selectedAnswers[currentQuestion.id] === text ? "selected" : ""} 
                    ${showFeedback && feedback?.is_correct && selectedAnswers[currentQuestion.id] === text ? "correct" : ""}
                    ${showFeedback && !feedback?.is_correct && selectedAnswers[currentQuestion.id] === text ? "wrong" : ""}
                  `}
                  onClick={() => handleSelect(currentQuestion.id, text)}
                >
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    value={text}
                    checked={selectedAnswers[currentQuestion.id] === text}
                    onChange={() => handleSelect(currentQuestion.id, text)}
                    style={{ display: "none" }}
                  />
                  {text}
                </label>
              );
            })}
          </div>

          {showFeedback && feedback && (
            <div
              className={`feedback ${
                feedback.is_correct ? "feedback-correto" : "feedback-incorreto"
              }`}
            >
              <p>
                <strong>Resposta:</strong>{" "}
                {feedback.is_correct ? "✔️ Correta" : "❌ Incorreta"}
              </p>

              <p>
                <strong>Alternativa escolhida:</strong> {feedback.chosen_option}
              </p>

              <p>
                <strong>Explicação:</strong>{" "}
                {feedback.is_correct
                  ? feedback.explanation
                  : feedback.explanation_chosen}
              </p>

              {!feedback.is_correct && (
                <>
                  <p>
                    <strong>Alternativa correta:</strong> {feedback.correct_option}
                  </p>
                  <p>
                    <strong>Por que está correta:</strong>{" "}
                    {feedback.explanation_correct}
                  </p>
                </>
              )}
            </div>
          )}

          <div className={`actions ${currentQuestionIndex === 0 ? "first-question" : ""}`}>
            {currentQuestionIndex > 0 && (
              <button className="back-button" onClick={handleBack}>
                Voltar
              </button>
            )}

            <button
              className={showFeedback ? "next-button" : "submit-button"}
              onClick={handleNext}
            >
              {showFeedback
                ? currentQuestionIndex < questions.length - 1
                  ? "Próxima"
                  : "Finalizar"
                : "Confirmar Resposta"}
            </button>
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
