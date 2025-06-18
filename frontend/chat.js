// Football ChatBot - JavaScript File
class FootballChatBot {
    constructor() {
        this.apiUrl = 'http://localhost:5000';
        this.requestCount = 0;
        this.maxRequests = 100;
        this.isLoading = false;
        this.popularTeams = [];
        this.quickStats = null;
        this.init();
    }

    init() {
        this.loadPopularTeams();
        this.loadQuickStats();
        this.updateStatus();
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Send message on Enter key
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Auto-resize input
            messageInput.addEventListener('input', (e) => {
                e.target.style.height = 'auto';
                e.target.style.height = (e.target.scrollHeight) + 'px';
            });
        }

        // Send button click
        const sendButton = document.getElementById('sendButton');
        if (sendButton) {
            sendButton.addEventListener('click', () => this.sendMessage());
        }
    }

    async loadPopularTeams() {
        try {
            const response = await fetch(`${this.apiUrl}/api/popular-teams`);
            if (response.ok) {
                const data = await response.json();
                this.popularTeams = data.teams;
                console.log('✅ Equipas populares carregadas:', this.popularTeams.length);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar equipas:', error);
        }
    }

    async loadQuickStats() {
        const statsLoading = document.getElementById('quickStatsLoading');
        const statsContent = document.getElementById('quickStatsContent');
        
        try {
            // Carregar classificação da Liga Portugal (ID: 94)
            const response = await fetch(`${this.apiUrl}/api/standings/94?season=2024`);
            
            if (response.ok) {
                const data = await response.json();
                const standings = data.standings;
                
                if (statsLoading) statsLoading.style.display = 'none';
                if (statsContent && standings && standings.length > 0) {
                    const leader = standings[0];
                    const topScorer = this.findTopScorer(standings);
                    
                    statsContent.innerHTML = `
                        <div class="stat-item">
                            <div class="stat-label">🏆 Líder da Liga</div>
                            <div class="stat-value">${leader.team.name}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">🎯 Pontos</div>
                            <div class="stat-value">${leader.points} pts</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">⚽ Jogos</div>
                            <div class="stat-value">${leader.all.played} jogados</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">🔥 Forma</div>
                            <div class="stat-value">${leader.form || 'N/A'}</div>
                        </div>
                    `;
                    statsContent.style.display = 'block';
                }
                
                // Atualizar contador de requests
                this.requestCount = data.requests_used || 0;
                this.updateRequestCounter();
                
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar estatísticas:', error);
            if (statsLoading) {
                statsLoading.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Erro ao carregar';
            }
        }
    }

    findTopScorer(standings) {
        return standings.reduce((top, team) => {
            return (team.all.goals.for > (top?.all?.goals?.for || 0)) ? team : top;
        }, null);
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput?.value.trim();
        
        if (!message || this.isLoading) return;
        
        if (this.requestCount >= this.maxRequests) {
            this.showError('Limite de requests atingido. Tente novamente mais tarde.');
            return;
        }

        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Add user message to chat
        this.addMessage(message, 'user');

        // Show loading
        this.setLoading(true);

        try {
            // Send to API
            const response = await fetch(`${this.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Update request count
            this.requestCount = data.requests_used || this.requestCount + 1;
            this.updateRequestCounter();

            // Add bot response
            this.addMessage(data.response, 'bot');

        } catch (error) {
            console.error('❌ Erro na API:', error);
            let errorMessage = 'Desculpe, ocorreu um erro. Tente novamente.';
            
            if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Erro de conexão. Verifique se o servidor está a funcionar.';
            } else if (error.message) {
                errorMessage = `Erro: ${error.message}`;
            }
            
            this.addMessage(errorMessage, 'bot', true);
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(text, sender, isError = false) {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const currentTime = new Date().toLocaleTimeString('pt-PT', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const avatar = sender === 'bot' ? 
            '<i class="fas fa-robot"></i>' : 
            '<i class="fas fa-user"></i>';

        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-text ${isError ? 'error' : ''}">
                    ${this.formatMessage(text)}
                </div>
                <div class="message-time">${currentTime}</div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(text) {
        // Convert markdown-like formatting to HTML
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraphs if not already wrapped
        if (!formatted.includes('<p>')) {
            formatted = `<p>${formatted}</p>`;
        }

        return formatted;
    }

    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendButton = document.getElementById('sendButton');
        const messageInput = document.getElementById('messageInput');
        const modal = document.getElementById('loadingModal');

        if (loading) {
            if (sendButton) {
                sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                sendButton.disabled = true;
            }
            if (messageInput) messageInput.disabled = true;
            if (modal) modal.classList.add('show');
        } else {
            if (sendButton) {
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
                sendButton.disabled = false;
            }
            if (messageInput) messageInput.disabled = false;
            if (modal) modal.classList.remove('show');
        }
    }

    updateRequestCounter() {
        const counter = document.getElementById('requestsCount');
        if (counter) {
            counter.textContent = `Requests: ${this.requestCount}/${this.maxRequests}`;
            
            // Update color based on usage
            if (this.requestCount >= this.maxRequests * 0.9) {
                counter.style.color = '#ef4444'; // Red
            } else if (this.requestCount >= this.maxRequests * 0.7) {
                counter.style.color = '#f59e0b'; // Orange
            } else {
                counter.style.color = '#10b981'; // Green
            }
        }
    }

    async updateStatus() {
        try {
            const response = await fetch(`${this.apiUrl}/api/status`);
            if (response.ok) {
                const data = await response.json();
                this.requestCount = data.requests_used || 0;
                this.updateRequestCounter();
                this.updateStatusIndicator(true);
            } else {
                this.updateStatusIndicator(false);
            }
        } catch (error) {
            console.error('❌ Erro ao verificar status:', error);
            this.updateStatusIndicator(false);
        }
    }

    updateStatusIndicator(online = true) {
        const indicator = document.getElementById('statusIndicator');
        if (indicator) {
            indicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
        }
    }

    showError(message) {
        this.addMessage(message, 'bot', true);
    }

    // Métodos para estatísticas específicas
    async getTeamStats(teamId, teamName) {
        try {
            const response = await fetch(`${this.apiUrl}/api/team/${teamId}/stats?league=94&season=2024`);
            if (response.ok) {
                const data = await response.json();
                return data.statistics;
            }
        } catch (error) {
            console.error(`❌ Erro ao obter stats do ${teamName}:`, error);
        }
        return null;
    }

    async getTeamMatches(teamId, teamName) {
        try {
            const response = await fetch(`${this.apiUrl}/api/team/${teamId}/matches?last=5`);
            if (response.ok) {
                const data = await response.json();
                return data.matches;
            }
        } catch (error) {
            console.error(`❌ Erro ao obter jogos do ${teamName}:`, error);
        }
        return null;
    }
}

// Quick action functions
function askAboutTeam(teamSlug) {
    const teamQuestions = {
        'benfica': 'Como está o Benfica esta época? Mostra-me estatísticas e últimos jogos.',
        'porto': 'Quero saber sobre o FC Porto. Como estão na classificação?',
        'sporting': 'Situação atual do Sporting CP na liga. Últimos resultados?',
        'braga': 'Como está o SC Braga? Mostra posição na tabela e estatísticas.'
    };
    
    const question = teamQuestions[teamSlug] || `Informações sobre ${teamSlug}`;
    askQuestion(question);
}

function askQuestion(question) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput && window.chatBot) {
        messageInput.value = question;
        messageInput.focus();
        
        // Trigger send after a small delay to allow the input to be filled
        setTimeout(() => {
            window.chatBot.sendMessage();
        }, 100);
    }
}

// Initialize app
function initializeApp() {
    // Create chatbot instance
    window.chatBot = new FootballChatBot();
    
    // Update status every 60 seconds
    setInterval(() => {
        window.chatBot.updateStatus();
    }, 60000);
    
    console.log('🚀 Football ChatBot inicializado!');
    console.log('🔗 API URL:', window.chatBot.apiUrl);
}

// Additional CSS for enhanced functionality
const additionalStyles = `
    .message-text.error {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%) !important;
        border-left: 4px solid #ef4444 !important;
        color: #dc2626;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.75rem 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        transition: background-color 0.2s ease;
    }
    
    .stat-item:hover {
        background-color: rgba(59, 130, 246, 0.05);
        border-radius: 6px;
        margin: 0 -0.5rem;
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
    
    .stat-item:last-child {
        border-bottom: none;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }
    
    .stat-value {
        font-weight: 600;
        color: #1e293b;
        font-size: 0.95rem;
    }
    
    .status-indicator.offline {
        background: #ef4444;
    }
    
    .modal.show {
        display: block !important;
    }
    
    /* Loading animation for stats */
    .stats-loading {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Enhanced message formatting */
    .message-text p {
        margin-bottom: 0.75rem;
    }
    
    .message-text p:last-child {
        margin-bottom: 0;
    }
    
    .message-text ul, .message-text ol {
        margin: 0.5rem 0;
        padding-left: 1.25rem;
    }
    
    .message-text li {
        margin-bottom: 0.25rem;
        line-height: 1.4;
    }
    
    /* Request counter colors */
    #requestsCount {
        transition: color 0.3s ease;
        font-weight: 500;
    }
`;

// Inject additional styles
document.addEventListener('DOMContentLoaded', function() {
    const style = document.createElement('style');
    style.textContent = additionalStyles;
    document.head.appendChild(style);
    
    // Initialize the app
    initializeApp();
});

// Export for global access
window.FootballChatBot = FootballChatBot;
window.askAboutTeam = askAboutTeam;
window.askQuestion = askQuestion;
window.initializeApp = initializeApp;