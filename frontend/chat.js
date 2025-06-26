// Football ChatBot - JavaScript File - VERSÃO ATUALIZADA PARA DADOS DA LIGA PORTUGAL
class FootballChatBot {
  constructor() {
    this.apiUrl = "http://localhost:5000";
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
      console.log("⚠️ ChatBot já foi inicializado");
      return;
    }

    console.log("🚀 Inicializando Football ChatBot...");
    this.setupEventListeners();

    // Carregar sidebar para a liga selecionada
    const leagueSelect = document.getElementById("leagueSelect");
    if (leagueSelect) {
      const leagueId = parseInt(leagueSelect.value);
      setTimeout(() => this.updateSidebarForLeague(leagueId), 100);
    }
    setTimeout(() => this.updateStatus(), 1000);

    this.isInitialized = true;
  }

  setupEventListeners() {
    // Send message on Enter key
    const messageInput = document.getElementById("messageInput");
    if (messageInput) {
      messageInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });

      // Auto-resize input
      messageInput.addEventListener("input", (e) => {
        e.target.style.height = "auto";
        e.target.style.height = e.target.scrollHeight + "px";
      });
    }

    // Send button click
    const sendButton = document.getElementById("sendButton");
    if (sendButton) {
      sendButton.addEventListener("click", () => this.sendMessage());
    }

    // Liga dropdown change
    const leagueSelect = document.getElementById("leagueSelect");
    if (leagueSelect) {
      leagueSelect.addEventListener("change", (e) => {
        const leagueId = parseInt(e.target.value);
        this.updateSidebarForLeague(leagueId);
      });
    }
  }

  formatForm(form) {
    if (!form) return "N/A";

    // Converter forma em ícones visuais
    return form
      .split("")
      .map((letter) => {
        switch (letter.toUpperCase()) {
          case "W":
            return "🟢"; // Vitória
          case "L":
            return "🔴"; // Derrota
          case "D":
            return "🟡"; // Empate
          default:
            return "⚪";
        }
      })
      .join("");
  }

  async updateSidebarForLeague(leagueId) {
    // Atualizar quick stats
    await this.loadQuickStats(leagueId);
    // Atualizar equipas populares
    await this.loadPopularTeamsByLeague(leagueId);
    // Atualizar perguntas rápidas
    this.updateQuickQuestions(leagueId);
  }

  async loadPopularTeamsByLeague(leagueId) {
    const requestKey = `popular-teams-${leagueId}`;
    if (this.pendingRequests.has(requestKey)) {
      console.log("⚠️ Request para equipas populares já está pendente");
      return;
    }
    this.pendingRequests.add(requestKey);
    const teamsContainer = document.querySelector(
      ".popular-teams .team-buttons"
    );
    const teamsTitle = document.querySelector(".popular-teams h3");
    if (teamsContainer)
      teamsContainer.innerHTML =
        '<div class="stats-loading"><i class="fas fa-spinner fa-spin"></i> Carregando...</div>';
    try {
      const response = await fetch(
        `${this.apiUrl}/api/popular-teams?league=${leagueId}`
      );
      if (response.ok) {
        const data = await response.json();
        const teams = data.teams || {};
        const teamSlugs = Object.keys(teams).slice(0, 5); // Apenas as 5 primeiras
        if (teamsTitle) {
          const leagueName = this.getLeagueNameById(leagueId);
          teamsTitle.innerHTML = `<i class="fas fa-star"></i> Equipas Populares`;
        }
        if (teamsContainer) {
          teamsContainer.innerHTML =
            teamSlugs
              .map((slug) => {
                const team = teams[slug];
                return `<button class="team-btn" onclick="askAboutTeam('${slug}')"><i class="fas fa-futbol"></i> ${this.capitalizeTeamName(
                  slug
                )}</button>`;
              })
              .join("") ||
            '<div style="color:#64748b">Sem equipas populares</div>';
        }
      } else {
        if (teamsContainer)
          teamsContainer.innerHTML =
            '<div style="color:#ef4444">Erro ao carregar equipas</div>';
      }
    } catch (error) {
      if (teamsContainer)
        teamsContainer.innerHTML =
          '<div style="color:#ef4444">Erro ao carregar equipas</div>';
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  async loadQuickStats(leagueId = 94) {
    const requestKey = `standings-${leagueId}`;
    if (this.pendingRequests.has(requestKey)) {
      console.log("⚠️ Request para standings já está pendente");
      return;
    }
    this.pendingRequests.add(requestKey);
    const statsLoading = document.getElementById("quickStatsLoading");
    const statsContent = document.getElementById("quickStatsContent");
    const statsTitle = document.querySelector(".quick-stats h3");
    try {
      if (statsLoading) {
        statsLoading.style.display = "block";
        statsLoading.innerHTML =
          '<i class="fas fa-spinner fa-spin"></i> Carregando...';
      }
      if (statsTitle) {
        const leagueName = this.getLeagueNameById(leagueId);
        statsTitle.innerHTML = `<i class="fas fa-chart-bar"></i> ${leagueName}`;
      }
      const response = await fetch(
        `${this.apiUrl}/api/standings/${leagueId}?season=2023`
      );
      if (response.ok) {
        const data = await response.json();
        const standings = data.standings || [];
        if (statsLoading) statsLoading.style.display = "none";
        if (statsContent) {
          if (standings && standings.length > 0) {
            const top3 = standings.slice(0, 3);
            const leader = standings[0];
            const bestAttack = standings.reduce((prev, current) =>
              prev.goals_for > current.goals_for ? prev : current
            );
            const bestDefense = standings.reduce((prev, current) =>
              prev.goals_against < current.goals_against ? prev : current
            );
            statsContent.innerHTML = `
                            <div class="stat-section">
                                <div class="stat-title">🏆 Top 3 Classificação</div>
                                ${top3
                                  .map(
                                    (team) => `
                                    <div class="stat-item ranking-item">
                                        <div class="position-badge">${team.position}º</div>
                                        <div class="team-info">
                                            <div class="team-name">${team.team.name}</div>
                                            <div class="team-points">${team.points} pts</div>
                                        </div>
                                    </div>
                                `
                                  )
                                  .join("")}
                            </div>
                            <div class="stat-section">
                                <div class="stat-item">
                                    <div class="stat-label">🎯 Líder</div>
                                    <div class="stat-value">${
                                      leader.team.name
                                    } (${leader.points} pts)</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-label">⚽ Melhor Ataque</div>
                                    <div class="stat-value">${
                                      bestAttack.team.name
                                    } (${bestAttack.goals_for})</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-label">🛡️ Melhor Defesa</div>
                                    <div class="stat-value">${
                                      bestDefense.team.name
                                    } (${bestDefense.goals_against})</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-label">🔥 Forma do Líder</div>
                                    <div class="stat-value">${this.formatForm(
                                      leader.form
                                    )}</div>
                                </div>
                            </div>
                        `;
            statsContent.style.display = "block";
          } else {
            statsContent.innerHTML =
              '<div style="color:#64748b; text-align:center; padding:1rem;">Sem dados de classificação para esta liga.</div>';
            statsContent.style.display = "block";
          }
        }
        this.requestCount = data.requests_used || 0;
        this.updateRequestCounter();
        this.retryAttempts = 0;
      } else {
        const errorText = await response.text();
        throw new Error(`Erro ${response.status}: ${errorText}`);
      }
    } catch (error) {
      if (statsLoading) {
        statsLoading.innerHTML = `<div style="color: #ef4444; text-align: center;"><i class="fas fa-exclamation-triangle"></i> Erro ao carregar classificação<br><small>Verifique a conexão com a API</small></div>`;
      }
      if (statsContent) {
        statsContent.innerHTML =
          '<div style="color:#64748b; text-align:center; padding:1rem;">Sem dados de classificação para esta liga.</div>';
        statsContent.style.display = "block";
      }
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  updateQuickQuestions(leagueId) {
    const quickQuestions = document.querySelector(
      ".quick-questions .question-buttons"
    );
    const leagueName = this.getLeagueNameById(leagueId);
    if (quickQuestions) {
      quickQuestions.innerHTML = `
                <button class="question-btn" onclick="askQuestion('Classificação da ${leagueName}')">
                    <i class="fas fa-trophy"></i> Classificação
                </button>
                <button class="question-btn" onclick="askQuestion('Quem está em primeiro lugar na ${leagueName}?')">
                    <i class="fas fa-crown"></i> Líder
                </button>
                <button class="question-btn" onclick="askQuestion('Clássico da ${leagueName}')">
                    <i class="fas fa-fire"></i> Clássico
                </button>
            `;
    }
  }

  getLeagueNameById(leagueId) {
    const leagueSelect = document.getElementById("leagueSelect");
    if (leagueSelect) {
      const option = leagueSelect.querySelector(`option[value="${leagueId}"]`);
      if (option) {
        return option.textContent.replace(/^\S+\s/, ""); // Remove emoji/flag
      }
    }
    return "Liga";
  }

  capitalizeTeamName(slug) {
    return slug.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  }

  async sendMessage() {
    const messageInput = document.getElementById("messageInput");
    const message = messageInput?.value.trim();
    if (!message || this.isLoading) return;
    if (this.requestCount >= this.maxRequests) {
      this.showError(
        "Limite de requests atingido. Tente novamente mais tarde."
      );
      return;
    }
    // Clear input
    messageInput.value = "";
    messageInput.style.height = "auto";
    // Add user message to chat
    this.addMessage(message, "user");
    // Show loading
    this.setLoading(true);
    try {
      // Obter o league_id selecionado
      const leagueSelect = document.getElementById("leagueSelect");
      const league_id = leagueSelect ? parseInt(leagueSelect.value) : 94;
      // Preparar o body com encoding explícito
      const requestBody = { question: message, league_id };
      const jsonString = JSON.stringify(requestBody);
      // Send to API
      const response = await fetch(`${this.apiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          Accept: "application/json",
          "Accept-Charset": "utf-8",
        },
        body: jsonString,
      });
      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Erro desconhecido" }));
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`
        );
      }
      const data = await response.json();
      this.requestCount = data.requests_used || this.requestCount + 1;
      this.updateRequestCounter();
      this.addMessage(data.response, "bot");
    } catch (error) {
      let errorMessage = "Desculpe, ocorreu um erro. Tente novamente.";
      if (error.message.includes("Failed to fetch")) {
        errorMessage =
          "Erro de conexão. Verifique se o servidor está a funcionar.";
      } else if (error.message.includes("500")) {
        errorMessage =
          "Erro interno do servidor. A API externa pode estar indisponível.";
      } else if (error.message) {
        errorMessage = `Erro: ${error.message}`;
      }
      this.addMessage(errorMessage, "bot", true);
    } finally {
      this.setLoading(false);
    }
  }

  addMessage(text, sender, isError = false) {
    const chatMessages = document.getElementById("chatMessages");
    if (!chatMessages) return;

    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${sender}-message`;

    const currentTime = new Date().toLocaleTimeString("pt-PT", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const avatar =
      sender === "bot"
        ? '<i class="fas fa-robot"></i>'
        : '<i class="fas fa-user"></i>';

    messageDiv.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-text ${isError ? "error" : ""}">
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
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\n\n/g, "</p><p>")
      .replace(/\n/g, "<br>");

    // Wrap in paragraphs if not already wrapped
    if (!formatted.includes("<p>")) {
      formatted = `<p>${formatted}</p>`;
    }

    return formatted;
  }

  scrollToBottom() {
    const chatMessages = document.getElementById("chatMessages");
    if (chatMessages) {
      setTimeout(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
      }, 100);
    }
  }

  setLoading(loading) {
    this.isLoading = loading;
    const sendButton = document.getElementById("sendButton");
    const messageInput = document.getElementById("messageInput");
    const modal = document.getElementById("loadingModal");

    if (loading) {
      if (sendButton) {
        sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        sendButton.disabled = true;
      }
      if (messageInput) messageInput.disabled = true;
      if (modal) modal.classList.add("show");
    } else {
      if (sendButton) {
        sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        sendButton.disabled = false;
      }
      if (messageInput) messageInput.disabled = false;
      if (modal) modal.classList.remove("show");
    }
  }

  updateRequestCounter() {
    const counter = document.getElementById("requestsCount");
    if (counter) {
      counter.textContent = `Requests: ${this.requestCount}/${this.maxRequests}`;

      // Update color based on usage
      if (this.requestCount >= this.maxRequests * 0.9) {
        counter.style.color = "#ef4444"; // Red
      } else if (this.requestCount >= this.maxRequests * 0.7) {
        counter.style.color = "#f59e0b"; // Orange
      } else {
        counter.style.color = "#10b981"; // Green
      }
    }
  }

  async updateStatus() {
    const requestKey = "status";
    if (this.pendingRequests.has(requestKey)) return;

    this.pendingRequests.add(requestKey);

    try {
      console.log("📡 Verificando status da API...");
      const response = await fetch(`${this.apiUrl}/api/status`);
      if (response.ok) {
        const data = await response.json();
        this.requestCount = data.requests_used || 0;
        this.updateRequestCounter();
        this.updateStatusIndicator(data.status === "online");
        console.log("✅ Status atualizado");
      } else {
        console.error("❌ Erro ao verificar status:", response.status);
        this.updateStatusIndicator(false);
      }
    } catch (error) {
      console.error("❌ Erro ao verificar status:", error);
      this.updateStatusIndicator(false);
    } finally {
      this.pendingRequests.delete(requestKey);
    }
  }

  updateStatusIndicator(online = true) {
    const indicator = document.getElementById("statusIndicator");
    if (indicator) {
      indicator.className = `status-indicator ${online ? "online" : "offline"}`;
    }
  }

  showError(message) {
    this.addMessage(message, "bot", true);
  }

  // Métodos para estatísticas específicas
  async getTeamStats(teamId, teamName) {
    try {
      const response = await fetch(
        `${this.apiUrl}/api/team/${teamId}/stats?league=94&season=2023`
      );
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
      const response = await fetch(
        `${this.apiUrl}/api/team/${teamId}/matches?last=5`
      );
      if (response.ok) {
        const data = await response.json();
        return data.matches;
      }
    } catch (error) {
      console.error(`❌ Erro ao obter jogos do ${teamName}:`, error);
    }
    return null;
  }

  // Nova função para enviar mensagem com params
  async sendMessageWithParams(message, league_id) {
    if (!message || this.isLoading) return;
    if (this.requestCount >= this.maxRequests) {
      this.showError(
        "Limite de requests atingido. Tente novamente mais tarde."
      );
      return;
    }
    this.addMessage(message, "user");
    this.setLoading(true);
    try {
      const requestBody = { question: message, league_id };
      const jsonString = JSON.stringify(requestBody);
      const response = await fetch(`${this.apiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          Accept: "application/json",
          "Accept-Charset": "utf-8",
        },
        body: jsonString,
      });
      if (!response.ok) {
        const errorData = await response
          .json()
          .catch(() => ({ error: "Erro desconhecido" }));
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`
        );
      }
      const data = await response.json();
      this.requestCount = data.requests_used || this.requestCount + 1;
      this.updateRequestCounter();
      this.addMessage(data.response, "bot");
    } catch (error) {
      let errorMessage = "Desculpe, ocorreu um erro. Tente novamente.";
      if (error.message.includes("Failed to fetch")) {
        errorMessage =
          "Erro de conexão. Verifique se o servidor está a funcionar.";
      } else if (error.message.includes("500")) {
        errorMessage =
          "Erro interno do servidor. A API externa pode estar indisponível.";
      } else if (error.message) {
        errorMessage = `Erro: ${error.message}`;
      }
      this.addMessage(errorMessage, "bot", true);
    } finally {
      this.setLoading(false);
    }
  }
}

function askAboutTeam(teamSlug) {
  const leagueSelect = document.getElementById("leagueSelect");
  const league_id = leagueSelect ? parseInt(leagueSelect.value) : 94;
  window.chatBot.sendMessageWithParams(`Como está o ${teamSlug}?`, league_id);
}

function askQuestion(question) {
  const leagueSelect = document.getElementById("leagueSelect");
  const league_id = leagueSelect ? parseInt(leagueSelect.value) : 94;
  window.chatBot.sendMessageWithParams(question, league_id);
}

// Função para limpar cache
function setupClearCacheButton() {
  const btn = document.getElementById("clearCacheBtn");
  if (!btn) return;
  btn.onclick = async () => {
    btn.disabled = true;
    const original = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    try {
      const resp = await fetch("http://localhost:5000/api/cache/clear", {
        method: "POST",
      });
      if (resp.ok) {
        btn.innerHTML =
          '<i class="fas fa-check-circle" style="color: #10b981"></i>';
        setTimeout(() => {
          btn.innerHTML = original;
          btn.disabled = false;
        }, 1500);
      } else {
        btn.innerHTML =
          '<i class="fas fa-times-circle" style="color: #ef4444"></i>';
        setTimeout(() => {
          btn.innerHTML = original;
          btn.disabled = false;
        }, 1500);
      }
    } catch {
      btn.innerHTML =
        '<i class="fas fa-times-circle" style="color: #ef4444"></i>';
      setTimeout(() => {
        btn.innerHTML = original;
        btn.disabled = false;
      }, 1500);
    }
  };
}

// Initialize app - COM PROTEÇÃO CONTRA MÚLTIPLAS INICIALIZAÇÕES
function initializeApp() {
  if (window.chatBot && window.chatBot.isInitialized) {
    console.log("⚠️ App já foi inicializado");
    return;
  }
  // Create chatbot instance
  window.chatBot = new FootballChatBot();
  // Atualizar sidebar para a liga selecionada no arranque
  const leagueSelect = document.getElementById("leagueSelect");
  if (leagueSelect) {
    const leagueId = parseInt(leagueSelect.value);
    // window.chatBot.updateSidebarForLeague(leagueId); @TODO:
  }
  // Update status every 60 seconds
  setInterval(() => {
    if (window.chatBot) {
      window.chatBot.updateStatus();
    }
  }, 60000);
  console.log("🚀 Football ChatBot inicializado!");
  console.log("🔗 API URL:", window.chatBot.apiUrl);
  setupClearCacheButton();
}

const additionalStyles = `
    .message-text.error {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%) !important;
        border-left: 4px solid #ef4444 !important;
        color: #dc2626;
    }
    
    .stat-section {
        margin-bottom: 1rem;
    }
    
    .stat-section:last-child {
        margin-bottom: 0;
    }
    
    .stat-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.75rem;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    .ranking-item {
        display: flex;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    }
    
    .ranking-item:last-child {
        border-bottom: none;
    }
    
    .position-badge {
        background: linear-gradient(135deg, #3b82f6, #1d4ed8);
        color: white;
        font-weight: bold;
        font-size: 0.8rem;
        padding: 0.25rem 0.5rem;
        border-radius: 50%;
        min-width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 0.75rem;
    }
    
    .position-badge:nth-child(1) {
        background: linear-gradient(135deg, #fbbf24, #f59e0b);
    }
    
    .team-info {
        flex: 1;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .team-name {
        font-weight: 600;
        color: #1e293b;
        font-size: 0.9rem;
    }
    
    .team-points {
        font-weight: 500;
        color: #3b82f6;
        font-size: 0.85rem;
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

document.addEventListener("DOMContentLoaded", function () {
  if (!document.getElementById("chatbot-styles")) {
    const style = document.createElement("style");
    style.id = "chatbot-styles";
    style.textContent = additionalStyles;
    document.head.appendChild(style);
  }

  initializeApp();
});

window.FootballChatBot = FootballChatBot;
window.askAboutTeam = askAboutTeam;
window.askQuestion = askQuestion;
window.initializeApp = initializeApp;
