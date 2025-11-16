import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./App";
import QuestionsPage from "./Components/QuestionPage/QuestionPage";
import ResultsPage from "./Components/ResultsPage/ResultsPage";
import ReviewPage from "./Components/ReviewPage/ReviewPage";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/questions" element={<QuestionsPage />} />
        <Route path="/resultado" element={<ResultsPage />} />
        <Route path="/review" element={<ReviewPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
