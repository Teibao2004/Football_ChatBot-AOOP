import re
import json
from typing import Dict, List, Optional
from football_manager import FootballDataManager

class FootballChatbot:
    """
    Chatbot inteligente para análise de futebol
    """
    
    def __init__(self, api_key: str):
        self.data_manager = FootballDataManager(api_key)
        
        # Mapeamento de equipas portuguesas
        self.portuguese_teams = {
            'benfica': {'id': 211, 'names': ['benfica', 'slb', 'águias']},
            'porto': {'id': 212, 'names': ['porto', 'fcp', 'dragões']},
            'sporting': {'id': 228, 'names': ['sporting', 'scp', 'leões']},
            'braga': {'id': 227, 'names': ['braga', 'sc braga', 'minhotos']},
            'vitória': {'id': 230, 'names': ['vitória', 'vsc', 'vitória guimarães']}
        }
        
        # Patterns de perguntas
        self.question_patterns = {
            'standings': [
                r'classificação', r'tabela', r'posição', r'ranking',
                r'quem está em primeiro', r'liderança'
            ],
            'team_stats': [
                r'estatísticas', r'stats', r'números', r'desempenho',
                r'como está', r'forma'
            ],
            'recent_matches': [
                r'últimos jogos', r'jogos recentes', r'forma recente',
                r'últimas partidas'
            ],
            'head_to_head': [
                r'vs', r'contra', r'histórico', r'confrontos',
                r'head to head', r'h2h'
            ],
            'players': [
                r'jogador', r'melhor marcador', r'goleador',
                r'assistências', r'cartões'
            ]
        }
    
    def process_question(self, question: str) -> str:
        """
        Processar pergunta do utilizador
        """
        question_lower = question.lower().strip()
        
        try:
            # Identificar tipo de pergunta
            question_type = self._classify_question(question_lower)
            
            # Processar baseado no tipo
            if question_type == 'standings':
                return self._handle_standings(question_lower)
            elif question_type == 'team_stats':
                return self._handle_team_stats(question_lower)
            elif question_type == 'recent_matches':
                return self._handle_recent_matches(question_lower)
            elif question_type == 'head_to_head':
                return self._handle_head_to_head(question_lower)
            elif question_type == 'players':
                return self._handle_players(question_lower)
            else:
                return self._handle_general(question_lower)
                
        except Exception as e:
            return f"😔 Desculpa, ocorreu um erro ao processar a tua pergunta: {str(e)}"
    
    def _classify_question(self, question: str) -> str:
        """
        Classificar tipo de pergunta
        """
        for question_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, question):
                    return question_type
        
        return 'general'
    
    def _identify_team(self, text: str) -> Optional[Dict]:
        """
        Identificar equipa no texto
        """
        for team, info in self.portuguese_teams.items():
            for name in info['names']:
                if name in text:
                    return {'name': team, 'id': info['id']}
        return None
    
    def _handle_standings(self, question: str) -> str:
        """
        Responder perguntas sobre classificações
        """
        # Assumir Liga Portugal por defeito
        standings = self.data_manager.get_standings(94, 2024)
        
        if not standings:
            return "😔 Não consegui obter a classificação no momento. Tenta novamente mais tarde."
        
        table = standings[0]['league']['standings'][0]
        
        # Se pergunta específica sobre uma equipa
        team = self._identify_team(question)
        if team:
            for pos, team_data in enumerate(table, 1):
                if team_data['team']['id'] == team['id']:
                    name = team_data['team']['name']
                    points = team_data['points']
                    played = team_data['all']['played']
                    wins = team_data['all']['win']
                    draws = team_data['all']['draw']
                    losses = team_data['all']['lose']
                    
                    return f"⚽ **{name}** está em **{pos}º lugar** na Liga Portugal!\n\n" \
                           f"📊 **Estatísticas:**\n" \
                           f"• Pontos: {points}\n" \
                           f"• Jogos: {played}\n" \
                           f"• Vitórias: {wins}\n" \
                           f"• Empates: {draws}\n" \
                           f"• Derrotas: {losses}"
        
        # Classificação geral (top 6)
        response = "🏆 **Classificação da Liga Portugal:**\n\n"
        
        for i, team_data in enumerate(table[:6]):
            pos = team_data['rank']
            name = team_data['team']['name']
            points = team_data['points']
            
            # Emojis baseados na posição
            if pos == 1:
                emoji = "🥇"
            elif pos == 2:
                emoji = "🥈"
            elif pos == 3:
                emoji = "🥉"
            elif pos <= 4:
                emoji = "🔵"  # Champions League
            elif pos <= 6:
                emoji = "🟡"  # Europa League
            else:
                emoji = "⚪"
            
            response += f"{emoji} **{pos}.** {name} - {points} pts\n"
        
        return response
    
    def _handle_team_stats(self, question: str) -> str:
        """
        Responder perguntas sobre estatísticas de equipas
        """
        team = self._identify_team(question)
        if not team:
            return "🤔 Não consegui identificar a equipa. Podes especificar? (ex: Benfica, Porto, Sporting)"
        
        stats = self.data_manager.get_team_statistics(team['id'], 94, 2024)
        if not stats:
            return f"😔 Não consegui obter as estatísticas do {team['name'].title()} no momento."
        
        # Extrair dados importantes
        fixtures = stats['fixtures']
        goals = stats['goals']
        team_name = stats['team']['name']
        
        # Calcular percentagens
        played = fixtures['played']['total']
        wins = fixtures['wins']['total']
        draws = fixtures['draws']['total']
        losses = fixtures['loses']['total']
        
        win_percentage = round((wins / played * 100), 1) if played > 0 else 0
        
        goals_for = goals['for']['total']['total']
        goals_against = goals['against']['total']['total']
        goal_difference = goals_for - goals_against
        
        response = f"⚽ **Estatísticas do {team_name}** (Liga Portugal 2024):\n\n"
        response += f"🎯 **Forma:**\n"
        response += f"• Jogos: {played}\n"
        response += f"• Vitórias: {wins} ({win_percentage}%)\n"
        response += f"• Empates: {draws}\n"
        response += f"• Derrotas: {losses}\n\n"
        
        response += f"⚽ **Golos:**\n"
        response += f"• Marcados: {goals_for}\n"
        response += f"• Sofridos: {goals_against}\n"
        response += f"• Diferença: {'+' if goal_difference >= 0 else ''}{goal_difference}\n\n"
        
        # Média de golos
        if played > 0:
            avg_for = round(goals_for / played, 1)
            avg_against = round(goals_against / played, 1)
            response += f"📈 **Médias por jogo:**\n"
            response += f"• Golos marcados: {avg_for}\n"
            response += f"• Golos sofridos: {avg_against}"
        
        return response
    
    def _handle_recent_matches(self, question: str) -> str:
        """
        Responder perguntas sobre jogos recentes
        """
        team = self._identify_team(question)
        if not team:
            return "🤔 De que equipa queres saber os últimos jogos?"
        
        matches = self.data_manager.get_recent_matches(team['id'], 5)
        if not matches:
            return f"😔 Não consegui obter os últimos jogos do {team['name'].title()}."
        
        team_name = team['name'].title()
        response = f"📅 **Últimos 5 jogos do {team_name}:**\n\n"
        
        for match in matches[:5]:
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            date = match['fixture']['date'][:10]  # YYYY-MM-DD
            
            # Determinar resultado para a equipa
            if match['teams']['home']['id'] == team['id']:
                # Equipa jogou em casa
                if home_goals > away_goals:
                    result = "✅"
                elif home_goals < away_goals:
                    result = "❌"
                else:
                    result = "⚪"
            else:
                # Equipa jogou fora
                if away_goals > home_goals:
                    result = "✅"
                elif away_goals < home_goals:
                    result = "❌"
                else:
                    result = "⚪"
            
            response += f"{result} {date}: {home_team} {home_goals}-{away_goals} {away_team}\n"
        
        return response
    
    def _handle_head_to_head(self, question: str) -> str:
        """
        Responder perguntas sobre confrontos diretos
        """
        # Tentar identificar duas equipas
        teams_found = []
        for team, info in self.portuguese_teams.items():
            for name in info['names']:
                if name in question:
                    teams_found.append({'name': team, 'id': info['id']})
                    break
        
        if len(teams_found) < 2:
            return "🤔 Preciso de duas equipas para mostrar o histórico. Ex: 'Benfica vs Porto'"
        
        team1 = teams_found[0]
        team2 = teams_found[1]
        
        h2h = self.data_manager.get_head_to_head(team1['id'], team2['id'])
        if not h2h:
            return f"😔 Não consegui obter o histórico entre {team1['name'].title()} e {team2['name'].title()}."
        
        response = f"⚔️ **{team1['name'].title()} vs {team2['name'].title()}** (Últimos confrontos):\n\n"
        
        team1_wins = 0
        team2_wins = 0
        draws = 0
        
        for match in h2h[:5]:  # Últimos 5 confrontos
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            date = match['fixture']['date'][:10]
            
            if home_goals > away_goals:
                if match['teams']['home']['id'] == team1['id']:
                    team1_wins += 1
                    result = "✅"
                else:
                    team2_wins += 1
                    result = "❌"
            elif home_goals < away_goals:
                if match['teams']['away']['id'] == team1['id']:
                    team1_wins += 1
                    result = "✅"
                else:
                    team2_wins += 1
                    result = "❌"
            else:
                draws += 1
                result = "⚪"
            
            response += f"{result} {date}: {home_team} {home_goals}-{away_goals} {away_team}\n"
        
        response += f"\n📊 **Balanço:**\n"
        response += f"• {team1['name'].title()}: {team1_wins} vitórias\n"
        response += f"• {team2['name'].title()}: {team2_wins} vitórias\n"
        response += f"• Empates: {draws}"
        
        return response
    
    def _handle_players(self, question: str) -> str:
        """
        Responder perguntas sobre jogadores (funcionalidade básica)
        """
        return "👥 **Estatísticas de jogadores em desenvolvimento!**\n\n" \
               "Por enquanto posso ajudar com:\n" \
               "• Classificações das equipas\n" \
               "• Estatísticas das equipas\n" \
               "• Últimos jogos\n" \
               "• Confrontos diretos\n\n" \
               "Tenta perguntar algo como: 'Como está o Benfica?' ou 'Classificação da Liga Portugal'"
    
    def _handle_general(self, question: str) -> str:
        """
        Responder perguntas gerais
        """
        # Verificar se menciona alguma equipa
        team = self._identify_team(question)
        if team:
            return self._handle_team_stats(question)
        
        return "🤖 **Olá! Sou o teu assistente de futebol português!** ⚽\n\n" \
               "Posso ajudar-te com:\n\n" \
               "🏆 **Classificações:**\n" \
               "• 'Classificação da Liga Portugal'\n" \
               "• 'Como está o Benfica na tabela?'\n\n" \
               "📊 **Estatísticas:**\n" \
               "• 'Estatísticas do Porto'\n" \
               "• 'Como está a forma do Sporting?'\n\n" \
               "📅 **Jogos Recentes:**\n" \
               "• 'Últimas derrotas do Braga'\n\n" \
               "⚔️ **Confrontos:**\n" \
               "• 'Benfica vs Porto histórico'\n\n" \
               "Faz a tua pergunta! 😊"