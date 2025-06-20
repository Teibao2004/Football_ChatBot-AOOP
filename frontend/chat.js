// Football ChatBot - JavaScript File - VERSÃO CORRIGIDA
class FootballChatBot {
    constructor() {
        this.apiUrl = 'http://localhost:5000';
        this.requestCount = 0;
        this.maxRequests = 100;
        this.isLoading = false;
        this.popularTeams = [];
        this.quickStats = null;
        this.isInitialized = false;
        this.pendingRequests = new Set(); // Para evitar requests duplicados
        this.retryAttempts = 0;
        this.maxRetries = 3;
        this.init();
    }

    init() {
        if (this.isInitialized) {
            console.log('⚠️ ChatBot já foi inicializado');
            return;
        }

        console.log('🚀 Inicializando Football ChatBot...');
        this.setupEventListeners();
        
        // Carregar dados com delay para evitar sobrecarga
        setTimeout(() => this.loadPopularTeams(), 100);
        setTimeout(() => this.loadQuickStats(), 500);
        setTimeout(() => this.updateStatus(), 1000);
        
        this.isInitialized = true;
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
        const requestKey = 'popular-teams';
        if (this.pendingRequests.has(requestKey)) {
            console.log('⚠️ Request para equipas populares já está pendente');
            return;
        }

        this.pendingRequests.add(requestKey);
        
        try {
            console.log('📡 Carregando equipas populares...');
            const response = await fetch(`${this.apiUrl}/api/popular-teams`);
            if (response.ok) {
                const data = await response.json();
                this.popularTeams = data.teams;
                console.log('✅ Equipas populares carregadas:', this.popularTeams.length);
            } else {
                console.error('❌ Erro HTTP ao carregar equipas:', response.status);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar equipas:', error);
        } finally {
            this.pendingRequests.delete(requestKey);
        }
    }

    async loadQuickStats() {
        const requestKey = 'standings-94';
        if (this.pendingRequests.has(requestKey)) {
            console.log('⚠️ Request para standings já está pendente');
            return;
        }

        this.pendingRequests.add(requestKey);
        const statsLoading = document.getElementById('quickStatsLoading');
        const statsContent = document.getElementById('quickStatsContent');
        
        try {
            console.log('📡 Carregando classificação da Liga Portugal...');
            
            // Mostrar loading
            if (statsLoading) {
                statsLoading.style.display = 'block';
                statsLoading.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Carregando...';
            }
            
            // Carregar classificação da Liga Portugal (ID: 94)
            const response = await fetch(`${this.apiUrl}/api/standings/94?season=2024`);
            
            console.log(`📊 Response status: ${response.status}`);
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Dados recebidos:', data);
                
                const standings = data.standings;
                
                if (statsLoading) statsLoading.style.display = 'none';
                
                if (statsContent && standings && standings.length > 0) {
                    const leader = standings[0];
                    
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
                    console.log('✅ Estatísticas atualizadas no DOM');
                } else {
                    throw new Error('Dados de classificação inválidos');
                }
                
                // Atualizar contador de requests
                this.requestCount = data.requests_used || 0;
                this.updateRequestCounter();
                this.retryAttempts = 0; // Reset retry counter on success
                
            } else {
                const errorText = await response.text();
                console.error('❌ Erro HTTP:', response.status, errorText);
                throw new Error(`Erro ${response.status}: ${errorText}`);
            }
        } catch (error) {
            console.error('❌ Erro ao carregar estatísticas:', error);
            
            // Retry logic
            if (this.retryAttempts < this.maxRetries) {
                this.retryAttempts++;
                console.log(`🔄 Tentativa ${this.retryAttempts}/${this.maxRetries} em 3 segundos...`);
                
                if (statsLoading) {
                    statsLoading.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Tentativa ${this.retryAttempts}/${this.maxRetries}...`;
                }
                
                setTimeout(() => {
                    this.pendingRequests.delete(requestKey);
                    this.loadQuickStats();
                }, 3000);
                return;
            }
            
            // Show error after all retries failed
            if (statsLoading) {
                statsLoading.innerHTML = `
                    <div style="color: #ef4444; text-align: center;">
                        <i class="fas fa-exclamation-triangle"></i> 
                        Erro ao carregar classificação
                        <br>
                        <small>Verifique a conexão com a API</small>
                    </div>
                `;
            }
        } finally {
            this.pendingRequests.delete(requestKey);
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
            console.log('📤 Enviando mensagem:', message);
            
            // Send to API
            const response = await fetch(`${this.apiUrl}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: message })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Erro desconhecido' }));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('📥 Resposta recebida:', data);
            
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
            } else if (error.message.includes('500')) {
                errorMessage = 'Erro interno do servidor. A API externa pode estar indisponível.';
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
        const requestKey = 'status';
        if (this.pendingRequests.has(requestKey)) return;
        
        this.pendingRequests.add(requestKey);
        
        try {
            console.log('📡 Verificando status da API...');
            const response = await fetch(`${this.apiUrl}/api/status`);
            if (response.ok) {
                const data = await response.json();
                this.requestCount = data.requests_used || 0;
                this.updateRequestCounter();
                this.updateStatusIndicator(true);
                console.log('✅ Status atualizado');
            } else {
                console.error('❌ Erro ao verificar status:', response.status);
                this.updateStatusIndicator(false);
            }
        } catch (error) {
            console.error('❌ Erro ao verificar status:', error);
            this.updateStatusIndicator(false);
        } finally {
            this.pendingRequests.delete(requestKey);
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

// Initialize app - COM PROTEÇÃO CONTRA MÚLTIPLAS INICIALIZAÇÕES
function initializeApp() {
    if (window.chatBot && window.chatBot.isInitialized) {
        console.log('⚠️ App já foi inicializado');
        return;
    }
    
    // Create chatbot instance
    window.chatBot = new FootballChatBot();
    
    // Update status every 60 seconds
    setInterval(() => {
        if (window.chatBot) {
            window.chatBot.updateStatus();
        }
    }, 60000);
    
    console.log('🚀 Football ChatBot inicializado!');
    console.log('🔗 API URL:', window.chatBot.apiUrl);
}

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

// Inject additional styles - COM PROTEÇÃO CONTRA DUPLICAÇÃO
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se os estilos já foram injetados
    if (!document.getElementById('chatbot-styles')) {
        const style = document.createElement('style');
        style.id = 'chatbot-styles';
        style.textContent = additionalStyles;
        document.head.appendChild(style);
    }
    
    // Initialize the app
    initializeApp();
});

// Export for global access
window.FootballChatBot = FootballChatBot;
window.askAboutTeam = askAboutTeam;
window.askQuestion = askQuestion;
window.initializeApp = initializeApp;