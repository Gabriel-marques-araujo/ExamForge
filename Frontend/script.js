const messagesContainer = document.getElementById('messages');
const inputBox = document.getElementById('question');
const sendBtn = document.getElementById('sendBtn');

const GENERATE_API_URL = 'http://127.0.0.1:8000/create/generate_mcq/';
const CHECK_API_URL = 'http://127.0.0.1:8000/create/check_answer/';


function addMessage(sender, text, isHTML = false) {
    const msg = document.createElement('div');
    msg.classList.add('message');
    msg.classList.add(sender === 'Você' ? 'user' : 'bot');
    msg.innerHTML = isHTML ? text : `<strong>${sender}:</strong> ${text}`;
    messagesContainer.appendChild(msg);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


async function sendMessage() {
    const topic = inputBox.value.trim();
    if (!topic) return;

    addMessage('Você', topic);
    inputBox.value = '';

    try {
        const response = await fetch(GENERATE_API_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({topic})
        });

        const data = await response.json();

        
        addMessage('ExameForg', `<strong>${data.question}</strong>`, true);

       
        data.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.textContent = opt.option;
            btn.style.display = 'block';
            btn.style.margin = '5px 0';

           
            btn.addEventListener('click', () => checkAnswer(topic, data.question, opt.option, data.options));

            messagesContainer.appendChild(btn);
        });

    } catch (err) {
        console.error(err);
        addMessage('ExameForg', 'Erro ao gerar questão.');
    }
}


async function checkAnswer(topic, question, chosenOption, options) {
    
    const correctOptionObj = options.find(opt => opt.is_correct);
    if (!correctOptionObj) return addMessage('ExameForg', 'Erro: alternativa correta não encontrada.');

    const correctOption = correctOptionObj.option;

    try {
        const response = await fetch(CHECK_API_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                topic: topic,             
                question: question,
                chosen_option: chosenOption,
                correct_option: correctOption
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            return addMessage('ExameForg', `Erro do servidor: ${errorText}`);
        }

        const data = await response.json();

        addMessage('Você', chosenOption);
        addMessage('ExameForg', data.explanation);

        
        const buttons = Array.from(messagesContainer.getElementsByTagName('button'));
        buttons.forEach(b => b.remove());

    } catch (err) {
        console.error(err);
        addMessage('ExameForg', 'Erro ao checar resposta.');
    }
}


sendBtn.addEventListener('click', sendMessage);
inputBox.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});
