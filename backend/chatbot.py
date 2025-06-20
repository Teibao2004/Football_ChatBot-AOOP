import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from football_manager import FootballDataManager

class FootballChatbot:
    """
    Chatbot inteligente para análise de futebol - Versão melhorada
    """
    
    def __init__(self, api_key: str = None):
        self.data_manager = FootballDataManager(api_key)
        
        # Patterns de perguntas mais abrangentes
        self.question_patterns = {
            'standings': [
                r'classificação', r'tabela', r'posição', r'ranking', r'lugar',
                r'quem está em primeiro', r'liderança', r'líder', r'topo',
                r'standings', r'table', r'position'
            ],
            'team_stats': [
                r'estatísticas', r'stats', r'números', r'desempenho',
                r'como está', r'forma', r'rendimento', r'performance',
                r'vitórias', r'derrotas', r'empates', r'golos'
            ],
            'recent_matches': [
                r'últimos jogos', r'jogos recentes', r'forma recente',
                r'últimas partidas', r'últimos resultados', r'resultados recentes',
                r'recent matches', r'last games'
            ],
            'next_matches': [
                r'próximos jogos', r'próximas partidas', r'calendário',
                r'quando joga', r'próximo jogo', r'agenda',
                r'next games', r'fixtures', r'schedule'
            ],
            'head_to_head': [
                r'vs', r'contra', r'histórico', r'confrontos',
                r'head to head', r'h2h', r'face a face'
            ],
            'live_matches': [
                r'ao vivo', r'live', r'agora', r'jogos hoje',
                r'em direto', r'directo', r'tempo real'
            ],
            'top_scorers': [
                r'melhor marcador', r'goleador', r'artilheiro',
                r'melhores marcadores', r'top scorer', r'goals'
            ],
            'league_info': [
                r'sobre a liga', r'informações da liga', r'liga',
                r'campeonato', r'torneio', r'competição'
            ]
        }
        
        # Comandos especiais
        self.special_commands = {
            'help': ['ajuda', 'help', 'comandos', 'o que podes fazer'],
            'leagues': ['ligas', 'campeonatos', 'leagues', 'competitions'],
            'cache': ['cache', 'limpar cache', 'clear cache'],
            'stats': ['estatísticas do bot', 'stats do bot', 'info']
        }
    
    def process_question(self, question: str) -> str:
        """
        Processar pergunta do utilizador com melhor análise contextual
        """
        question_lower = question.lower().strip()
        
        try:
            # Verificar comandos especiais primeiro
            special_response = self._handle_special_commands(question_lower)
            if special_response:
                return special_response
            
            # Identificar tipo de pergunta
            question_type = self._classify_question(question_lower)
            
            # Identificar liga e equipa no contexto
            league_info = self._identify_league(question_lower)
            team_info = self._identify_team(question_lower, league_info['id'] if league_info else None)
            
            # Processar baseado no tipo
            if question_type == 'standings':
                return self._handle_standings(question_lower, league_info, team_info)
            elif question_type == 'team_stats':
                return self._handle_team_stats(question_lower, team_info, league_info)
            elif question_type == 'recent_matches':
                return self._handle_recent_matches(question_lower, team_info, league_info)
            elif question_type == 'next_matches':
                return self._handle_next_matches(question_lower, team_info, league_info)
            elif question_type == 'head_to_head':
                return self._handle_head_to_head(question_lower)
            elif question_type == 'live_matches':
                return self._handle_live_matches(question_lower, league_info)
            elif question_type == 'top_scorers':
                return self._handle_top_scorers(question_lower, league_info)
            elif question_type == 'league_info':
                return self._handle_league_info(question_lower, league_info)
            else:
                return self._handle_general(question_lower, team_info, league_info)
                
        except Exception as e:
            return f"😔 Desculpa, ocorreu um erro ao processar a tua pergunta: {str(e)}\n\nTenta reformular ou escreve 'ajuda' para ver os comandos disponíveis."
    
    def _handle_special_commands(self, question: str) -> Optional[str]:
        """
        Lidar com comandos especiais
        """
        for command, triggers in self.special_commands.items():
            for trigger in triggers:
                if trigger in question:
                    if command == 'help':
                        return self._show_help()
                    elif command == 'leagues':
                        return self._show_available_leagues()
                    elif command == 'cache':
                        return self._handle_cache_command()
                    elif command == 'stats':
                        return self._show_bot_stats()
        return None
    
    def _classify_question(self, question: str) -> str:
        """
        Classificar tipo de pergunta com pontuação
        """
        scores = {}
        
        for question_type, patterns in self.question_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, question))
                score += matches
            scores[question_type] = score
        
        # Retornar o tipo com maior pontuação
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'general'
    
    def _identify_league(self, text: str) -> Optional[Dict]:
        """
        Identificar liga no texto
        """
        return self.data_manager.identify_league_by_name(text)
    
    def _identify_team(self, text: str, league_id: int = None) -> Optional[Dict]:
        """
        Identificar equipa no texto
        """
        return self.data_manager.identify_team_by_name(text, league_id)
    
    def _handle_standings(self, question: str, league_info: Dict = None, team_info: Dict = None) -> str:
        """
        Responder perguntas sobre classificações
        """
        # Determinar liga (padrão: Liga Portugal)
        league_id = league_info['id'] if league_info else 94
        league_name = league_info['name'] if league_info else 'Liga Portugal'
        league_flag = league_info['flag'] if league_info else '🇵🇹'
        
        standings = self.data_manager.get_standings(league_id, 2024)
        
        if not standings:
            return f"😔 Não consegui obter a classificação da {league_name} no momento. Tenta novamente mais tarde."
        
        table = standings[0]['league']['standings'][0]
        
        # Se pergunta específica sobre uma equipa
        if team_info:
            for team_data in table:
                if team_data['team']['id'] == team_info['id']:
                    pos = team_data['rank']
                    name = team_data['team']['name']
                    points = team_data['points']
                    played = team_data['all']['played']
                    wins = team_data['all']['win']
                    draws = team_data['all']['draw']
                    losses = team_data['all']['lose']
                    goals_for = team_data['all']['goals']['for']
                    goals_against = team_data['all']['goals']['against']
                    goal_diff = goals_for - goals_against
                    
                    # Status baseado na posição
                    if pos == 1:
                        status = "🥇 **LÍDER!**"
                    elif pos <= 4 and league_id in [94, 39, 140, 78, 135, 61]:
                        status = "🔵 **Champions League**"
                    elif pos <= 6 and league_id in [94, 39, 140, 78, 135, 61]:
                        status = "🟡 **Europa League**"
                    elif pos >= len(table) - 2:
                        status = "🔴 **Zona de Descida**"
                    else:
                        status = f"⚪ **{pos}º lugar**"
                    
                    return f"{league_flag} **{name}** na {league_name}\n\n" \
                           f"{status}\n\n" \
                           f"📊 **Estatísticas:**\n" \
                           f"• **Posição:** {pos}º\n" \
                           f"• **Pontos:** {points}\n" \
                           f"• **Jogos:** {played}\n" \
                           f"• **Vitórias:** {wins}\n" \
                           f"• **Empates:** {draws}\n" \
                           f"• **Derrotas:** {losses}\n" \
                           f"• **Golos:** {goals_for}:{goals_against} ({'+' if goal_diff >= 0 else ''}{goal_diff})"
        
        # Classificação geral
        response = f"{league_flag} **Classificação da {league_name}:**\n\n"
        
        # Mostrar top 8 ou toda a tabela se for pequena
        display_count = min(8, len(table))
        
        for i, team_data in enumerate(table[:display_count]):
            pos = team_data['rank']
            name = team_data['team']['name']
            points = team_data['points']
            played = team_data['all']['played']
            
            # Emojis baseados na posição e liga
            if pos == 1:
                emoji = "🥇"
            elif pos == 2:
                emoji = "🥈"
            elif pos == 3:
                emoji = "🥉"
            elif pos <= 4 and league_id in [94, 39, 140, 78, 135, 61]:
                emoji = "🔵"  # Champions League
            elif pos <= 6 and league_id in [94, 39, 140, 78, 135, 61]:
                emoji = "🟡"  # Europa League
            elif pos >= len(table) - 2:
                emoji = "🔴"  # Descida
            else:
                emoji = "⚪"
            
            response += f"{emoji} **{pos}.** {name} - {points} pts ({played}j)\n"
        
        if len(table) > display_count:
            response += f"\n... e mais {len(table) - display_count} equipas"
        
        return response
    
    def _handle_team_stats(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre estatísticas de equipas
        """
        if not team_info:
            return "🤔 Não consegui identificar a equipa. Podes especificar? (ex: Benfica, Real Madrid, Manchester United)"
        
        # Determinar liga
        league_id = team_info.get('league') or (league_info['id'] if league_info else 94)
        
        stats = self.data_manager.get_team_statistics(team_info['id'], league_id, 2024)
        if not stats:
            team_name = team_info.get('name', 'equipa').title()
            return f"😔 Não consegui obter as estatísticas do {team_name} no momento."
        
        # Extrair dados
        fixtures = stats['fixtures']
        goals = stats['goals']
        team_name = stats['team']['name']
        league_name = stats['league']['name']
        
        played = fixtures['played']['total']
        wins = fixtures['wins']['total']
        draws = fixtures['draws']['total']
        losses = fixtures['loses']['total']
        
        goals_for = goals['for']['total']['total']
        goals_against = goals['against']['total']['total']
        goal_difference = goals_for - goals_against
        
        # Calcular percentagens e médias
        win_percentage = round((wins / played * 100), 1) if played > 0 else 0
        avg_goals_for = round(goals_for / played, 1) if played > 0 else 0
        avg_goals_against = round(goals_against / played, 1) if played > 0 else 0
        
        # Forma recente (baseada em percentagem de vitórias)
        if win_percentage >= 70:
            form_emoji = "🔥"
            form_text = "Excelente"
        elif win_percentage >= 50:
            form_emoji = "✅"
            form_text = "Boa"
        elif win_percentage >= 30:
            form_emoji = "⚠️"
            form_text = "Irregular"
        else:
            form_emoji = "❌"
            form_text = "Má"
        
        response = f"⚽ **{team_name}** ({league_name} 2024):\n\n"
        response += f"{form_emoji} **Forma: {form_text}** ({win_percentage}% vitórias)\n\n"
        
        response += f"🎯 **Resultados:**\n"
        response += f"• **Jogos:** {played}\n"
        response += f"• **Vitórias:** {wins}\n"
        response += f"• **Empates:** {draws}\n"
        response += f"• **Derrotas:** {losses}\n\n"
        
        response += f"⚽ **Golos:**\n"
        response += f"• **Marcados:** {goals_for} (média: {avg_goals_for})\n"
        response += f"• **Sofridos:** {goals_against} (média: {avg_goals_against})\n"
        response += f"• **Diferença:** {'+' if goal_difference >= 0 else ''}{goal_difference}\n"
        
        # Estatísticas adicionais se disponíveis
        if 'cards' in stats:
            yellow = stats['cards']['yellow']['total']
            red = stats['cards']['red']['total']
            if yellow or red:
                response += f"\n🟨 **Disciplina:**\n"
                response += f"• Cartões amarelos: {yellow}\n"
                response += f"• Cartões vermelhos: {red}"
        
        return response
    
    def _handle_recent_matches(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre jogos recentes
        """
        if not team_info and not league_info:
            return "🤔 De que equipa ou liga queres saber os últimos jogos?"
        
        if team_info:
            # Jogos de uma equipa específica
            matches = self.data_manager.get_recent_matches(team_info['id'], 5)
            if not matches:
                team_name = team_info.get('name', 'equipa').title()
                return f"😔 Não consegui obter os últimos jogos do {team_name}."
            
            team_name = team_info.get('name', 'equipa').title()
            response = f"📅 **Últimos 5 jogos do {team_name}:**\n\n"
            
            for match in matches[:5]:
                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']
                home_goals = match['goals']['home'] if match['goals']['home'] is not None else 0
                away_goals = match['goals']['away'] if match['goals']['away'] is not None else 0
                date = match['fixture']['date'][:10]
                status = match['fixture']['status']['short']
                
                # Se jogo não terminou
                if status not in ['FT', 'AET', 'PEN']:
                    continue
                
                # Determinar resultado para a equipa
                if match['teams']['home']['id'] == team_info['id']:
                    if home_goals > away_goals:
                        result = "✅"
                    elif home_goals < away_goals:
                        result = "❌"
                    else:
                        result = "⚪"
                else:
                    if away_goals > home_goals:
                        result = "✅"
                    elif away_goals < home_goals:
                        result = "❌"
                    else:
                        result = "⚪"
                
                response += f"{result} **{date}:** {home_team} {home_goals}-{away_goals} {away_team}\n"
            
        else:
            # Jogos recentes de uma liga
            league_id = league_info['id']
            league_name = league_info['name']
            matches = self.data_manager.get_fixtures_by_league(league_id, 2024, 10)
            
            if not matches:
                return f"😔 Não consegui obter os últimos jogos da {league_name}."
            
            # Filtrar apenas jogos terminados
            finished_matches = [m for m in matches if m['fixture']['status']['short'] in ['FT', 'AET', 'PEN']][:5]
            
            response = f"📅 **Últimos jogos da {league_name}:**\n\n"
            
            for match in finished_matches:
                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']
                home_goals = match['goals']['home']
                away_goals = match['goals']['away']
                date = match['fixture']['date'][:10]
                
                response += f"**{date}:** {home_team} {home_goals}-{away_goals} {away_team}\n"
        
        return response
    
    def _handle_next_matches(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre próximos jogos
        """
        if not team_info and not league_info:
            return "🤔 De que equipa ou liga queres saber os próximos jogos?"
        
        if team_info:
            # Próximos jogos de uma equipa
            matches = self.data_manager.get_next_fixtures(team_id=team_info['id'], next=5)
            if not matches:
                team_name = team_info.get('name', 'equipa').title()
                return f"😔 Não consegui obter os próximos jogos do {team_name}."
            
            team_name = team_info.get('name', 'equipa').title()
            response = f"📅 **Próximos 5 jogos do {team_name}:**\n\n"
            
            for match in matches[:5]:
                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']
                date = match['fixture']['date'][:16].replace('T', ' ')
                league = match['league']['name']
                
                # Destacar se é casa ou fora
                if match['teams']['home']['id'] == team_info['id']:
                    venue = "🏠"
                else:
                    venue = "✈️"
                
                response += f"{venue} **{date}:** {home_team} vs {away_team}\n"
                response += f"    📍 {league}\n\n"
        
        else:
            # Próximos jogos de uma liga
            league_id = league_info['id']
            league_name = league_info['name']
            matches = self.data_manager.get_next_fixtures(league_id=league_id, next=10)
            
            if not matches:
                return f"😔 Não consegui obter os próximos jogos da {league_name}."
            
            response = f"📅 **Próximos jogos da {league_name}:**\n\n"
            
            for match in matches[:5]:
                home_team = match['teams']['home']['name']
                away_team = match['teams']['away']['name']
                date = match['fixture']['date'][:16].replace('T', ' ')
                
                response += f"**{date}:** {home_team} vs {away_team}\n"
        
        return response
    
    def _handle_head_to_head(self, question: str) -> str:
        """
        Responder perguntas sobre confrontos diretos
        """
        # Tentar identificar duas equipas
        teams_found = []
        words = question.split()
        
        for i, word in enumerate(words):
            team = self.data_manager.identify_team_by_name(word)
            if team and team not in teams_found:
                teams_found.append(team)
                if len(teams_found) == 2:
                    break
        
        # Se não encontrou duas equipas, tentar padrões específicos
        if len(teams_found) < 2:
            # Procurar padrões como "benfica vs porto"
            vs_patterns = [r'(.+?)\s+vs\s+(.+)', r'(.+?)\s+contra\s+(.+)', r'(.+?)\s+x\s+(.+)']
            
            for pattern in vs_patterns:
                match = re.search(pattern, question)
                if match:
                    team1_name = match.group(1).strip()
                    team2_name = match.group(2).strip()
                    
                    team1 = self.data_manager.identify_team_by_name(team1_name)
                    team2 = self.data_manager.identify_team_by_name(team2_name)
                    
                    if team1 and team2:
                        teams_found = [team1, team2]
                        break
        
        if len(teams_found) < 2:
            return "🤔 Preciso de duas equipas para mostrar o histórico. Ex: 'Benfica vs Porto' ou 'Real Madrid contra Barcelona'"
        
        team1 = teams_found[0]
        team2 = teams_found[1]
        
        h2h = self.data_manager.get_head_to_head(team1['id'], team2['id'], 8)
        if not h2h:
            return f"😔 Não consegui obter o histórico entre {team1['name']} e {team2['name']}."
        
        team1_name = team1['name'] if isinstance(team1['name'], str) else str(team1['name']).title()
        team2_name = team2['name'] if isinstance(team2['name'], str) else str(team2['name']).title()
        
        response = f"⚔️ **{team1_name} vs {team2_name}** (Últimos confrontos):\n\n"
        
        team1_wins = 0
        team2_wins = 0
        draws = 0
        
        # Analisar últimos 5 jogos
        recent_matches = []
        for match in h2h[:5]:
            if match['fixture']['status']['short'] in ['FT', 'AET', 'PEN']:
                recent_matches.append(match)
        
        for match in recent_matches:
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_goals = match['goals']['home']
            away_goals = match['goals']['away']
            date = match['fixture']['date'][:10]
            league = match['league']['name']
            
            # Determinar vencedor
            if home_goals > away_goals:
                winner_id = match['teams']['home']['id']
            elif home_goals < away_goals:
                winner_id = match['teams']['away']['id']
            else:
                winner_id = None
            
            # Contabilizar resultado
            if winner_id == team1['id']:
                team1_wins += 1
                result = "✅" if match['teams']['home']['id'] == team1['id'] else "✅"
            elif winner_id == team2['id']:
                team2_wins += 1
                result = "❌" if match['teams']['home']['id'] == team1['id'] else "❌"
            else:
                draws += 1
                result = "⚪"
            
            response += f"{result} **{date}** ({league}):\n"
            response += f"    {home_team} {home_goals}-{away_goals} {away_team}\n\n"
        
        # Resumo do balanço
        total_games = team1_wins + team2_wins + draws
        response += f"📊 **Balanço (últimos {total_games} jogos):**\n"
        response += f"• **{team1_name}:** {team1_wins} vitórias\n"
        response += f"• **{team2_name}:** {team2_wins} vitórias\n"
        response += f"• **Empates:** {draws}"
        
        return response
    
    def _handle_live_matches(self, question: str, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre jogos ao vivo
        """
        league_id = league_info['id'] if league_info else None
        live_matches = self.data_manager.get_live_fixtures(league_id)
        
        if not live_matches:
            league_text = f"da {league_info['name']}" if league_info else ""
            return f"📺 Não há jogos ao vivo {league_text} neste momento."
        
        league_text = f"da {league_info['name']}" if league_info else ""
        response = f"📺 **Jogos ao vivo {league_text}:**\n\n"
        
        for match in live_matches[:10]:  # Limitar a 10 jogos
            home_team = match['teams']['home']['name']
            away_team = match['teams']['away']['name']
            home_goals = match['goals']['home'] or 0
            away_goals = match['goals']['away'] or 0
            elapsed = match['fixture']['status']['elapsed']
            league = match['league']['name']
            
            status_emoji = "🔴" if match['fixture']['status']['short'] in ['1H', '2H'] else "⏸️"
            
            response += f"{status_emoji} **{home_team} {home_goals}-{away_goals} {away_team}**\n"
            response += f"    ⏱️ {elapsed}' | 📍 {league}\n\n"
        
        return response
    
    def _handle_top_scorers(self, question: str, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre melhores marcadores
        """
        league_id = league_info['id'] if league_info else 94
        league_name = league_info['name'] if league_info else 'Liga Portugal'
        
        top_scorers = self.data_manager.get_top_scorers(league_id, 2024)
        
        if not top_scorers:
            return f"😔 Não consegui obter os melhores marcadores da {league_name} no momento."
        
        response = f"⚽ **Melhores Marcadores da {league_name}:**\n\n"
        
        for i, player in enumerate(top_scorers[:10], 1):
            name = player['player']['name']
            team = player['statistics'][0]['team']['name']
            goals = player['statistics'][0]['goals']['total']
            
            # Emojis para o pódium
            if i == 1:
                emoji = "🥇"
            elif i == 2:
                emoji = "🥈"
            elif i == 3:
                emoji = "🥉"
            else:
                emoji = f"{i}."
            
            response += f"{emoji} **{name}** ({team}) - {goals} golos\n"
        
        return response
    
    def _handle_league_info(self, question: str, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre informações da liga
        """
        if not league_info:
            return self._show_available_leagues()
        
        league_name = league_info['name']
        league_flag = league_info['flag']
        country = league_info['country']
        
        response = f"{league_flag} **{league_name}** ({country})\n\n"
        
        # Tentar obter estatísticas da liga
        standings = self.data_manager.get_standings(league_info['id'], 2024)
        if standings:
            table = standings[0]['league']['standings'][0]
            total_teams = len(table)
            
            # Calcular estatísticas gerais
            total_played = sum(team['all']['played'] for team in table)
            total_goals = sum(team['all']['goals']['for'] for team in table)
            
            response += f"📊 **Estatísticas da Temporada:**\n"
            response += f"• **Equipas:** {total_teams}\n"
            response += f"• **Jogos disputados:** {total_played}\n"
            response += f"• **Golos marcados:** {total_goals}\n"
            response += f"• **Média de golos por jogo:** {round(total_goals/total_played*2, 1) if total_played > 0 else 0}\n\n"
            
            # Líder atual
            leader = table[0]
            response += f"🥇 **Líder atual:** {leader['team']['name']} ({leader['points']} pts)"
        
        return response
    
    def _handle_general(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas gerais ou tentar inferir intenção
        """
        # Se menciona uma equipa, mostrar estatísticas gerais
        if team_info:
            return self._handle_team_stats(question, team_info, league_info)
        
        # Se menciona uma liga, mostrar classificação
        if league_info:
            return self._handle_standings(question, league_info)
        
        # Tentar identificar se é uma pergunta sobre futebol em geral
        football_keywords = ['futebol', 'jogo', 'golo', 'resultado', 'football', 'soccer', 'match', 'goal']
        
        if any(keyword in question.lower() for keyword in football_keywords):
            return "⚽ Posso ajudar-te com informações sobre futebol!\n\n" \
                   "Algumas coisas que podes perguntar:\n" \
                   "• Classificação de uma liga\n" \
                   "• Estatísticas de uma equipa\n" \
                   "• Últimos ou próximos jogos\n" \
                   "• Histórico entre equipas\n" \
                   "• Melhores marcadores\n" \
                   "• Jogos ao vivo\n\n" \
                   "Escreve 'ajuda' para ver todos os comandos disponíveis!"
        
        # Resposta padrão para perguntas não relacionadas com futebol
        return "🤔 Não consegui entender a tua pergunta sobre futebol.\n\n" \
               "Podes perguntar sobre:\n" \
               "• Uma equipa específica (ex: 'Como está o Benfica?')\n" \
               "• Uma liga (ex: 'Classificação da Premier League')\n" \
               "• Jogos (ex: 'Próximos jogos do Porto')\n\n" \
               "Escreve 'ajuda' para ver todos os comandos!"
    
    def _show_help(self) -> str:
        """
        Mostrar ajuda com comandos disponíveis
        """
        return """🤖 **Ajuda do Football Chatbot**

**📊 Classificações e Tabelas:**
• "classificação da liga portugal"
• "tabela da premier league"
• "posição do benfica"

**⚽ Estatísticas de Equipas:**
• "estatísticas do real madrid"
• "como está o manchester united"
• "números do barcelona"

**📅 Jogos e Calendário:**
• "últimos jogos do porto"
• "próximas partidas do sporting"
• "quando joga o arsenal"

**⚔️ Confrontos Diretos:**
• "benfica vs porto"
• "real madrid contra barcelona"
• "histórico arsenal x tottenham"

**🏆 Melhores Marcadores:**
• "melhor marcador da la liga"
• "goleadores da serie a"

**📺 Jogos ao Vivo:**
• "jogos ao vivo"
• "live premier league"

**🌍 Ligas Disponíveis:**
• Portugal, Inglaterra, Espanha, Alemanha
• Itália, França, Holanda, Brasil, Argentina
• Champions League, Europa League, Conference League

**⚙️ Comandos Especiais:**
• `ligas` - Ver todas as ligas
• `cache` - Limpar cache
• `stats` - Estatísticas do bot

💡 **Dica:** Podes fazer perguntas naturais em português ou inglês!"""
    
    def _show_available_leagues(self) -> str:
        """
        Mostrar ligas disponíveis
        """
        response = "🌍 **Ligas Disponíveis:**\n\n"
        
        for league_key, league_info in self.data_manager.available_leagues.items():
            flag = league_info['flag']
            name = league_info['name']
            country = league_info['country']
            response += f"{flag} **{name}** ({country})\n"
        
        response += "\n💡 **Como usar:**\n"
        response += "• 'classificação da premier league'\n"
        response += "• 'melhores marcadores da serie a'\n"
        response += "• 'jogos ao vivo da champions league'"
        
        return response
    
    def _handle_cache_command(self) -> str:
        """
        Lidar com comandos de cache
        """
        stats = self.data_manager.get_cache_stats()
        
        response = "🗄️ **Estatísticas do Cache:**\n\n"
        response += f"• **Total de entradas:** {stats['total_entries']}\n"
        response += f"• **Entradas ativas:** {stats['active_entries']}\n"
        response += f"• **Entradas expiradas:** {stats['expired_entries']}\n"
        response += f"• **Requests feitos:** {stats['requests_made']}/100\n"
        response += f"• **Requests restantes:** {stats['requests_remaining']}\n\n"
        
        if stats['expired_entries'] > 0:
            response += "💡 Há entradas expiradas no cache. Quer limpar?\n"
            response += "Escreve 'limpar cache' para limpar."
        
        return response
    
    def _show_bot_stats(self) -> str:
        """
        Mostrar estatísticas do bot
        """
        cache_stats = self.data_manager.get_cache_stats()
        
        response = "📊 **Estatísticas do Football Bot:**\n\n"
        response += f"🔢 **API Requests:** {cache_stats['requests_made']}/100 diários\n"
        response += f"🗄️ **Cache:** {cache_stats['active_entries']} entradas ativas\n"
        response += f"🌍 **Ligas:** {len(self.data_manager.available_leagues)} disponíveis\n"
        response += f"⚽ **Equipas:** {sum(len(teams) for teams in self.data_manager.popular_teams.values())} populares\n\n"
        
        response += "🏆 **Ligas Mais Populares:**\n"
        popular_leagues = ['portugal', 'england', 'spain', 'germany', 'italy']
        for league_key in popular_leagues:
            if league_key in self.data_manager.available_leagues:
                league_info = self.data_manager.available_leagues[league_key]
                response += f"• {league_info['flag']} {league_info['name']}\n"
        
        response += f"\n⏱️ **Cache Duration:** {self.data_manager.cache_duration} horas"
        
        return response

    def get_conversation_context(self) -> str:
        """
        Obter contexto para conversação contínua
        """
        return """🤖 **Football Chatbot - Assistente de Futebol**

Olá! Sou o teu assistente de futebol inteligente. Posso ajudar-te com:

⚽ **Informações em Tempo Real:**
• Classificações e tabelas
• Estatísticas de equipas
• Resultados e calendários
• Confrontos diretos
• Melhores marcadores
• Jogos ao vivo

🌍 **Ligas Cobertas:**
• Liga Portugal, Premier League, La Liga
• Bundesliga, Serie A, Ligue 1
• Champions League, Europa League
• E muito mais!

💬 **Como Usar:**
Faz perguntas naturais como:
• "Como está o Benfica?"
• "Classificação da Premier League"
• "Benfica vs Porto histórico"
• "Próximos jogos do Real Madrid"

Escreve 'ajuda' para ver todos os comandos disponíveis!"""

# Classe principal para interface simplificada
class FootballChatInterface:
    """
    Interface simplificada para o chatbot
    """
    
    def __init__(self, api_key: str = None):
        try:
            self.chatbot = FootballChatbot(api_key)
            self.running = True
            print(self.chatbot.get_conversation_context())
        except Exception as e:
            print(f"❌ Erro ao inicializar o chatbot: {e}")
            self.running = False
    
    def start_chat(self):
        """
        Iniciar conversa interativa
        """
        if not self.running:
            return
            
        print("\n" + "="*60)
        print("🤖 Football Chatbot iniciado! Digite 'sair' para terminar.")
        print("="*60)
        
        while self.running:
            try:
                user_input = input("\n🗣️  Tu: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['sair', 'exit', 'quit', 'bye']:
                    print("\n👋 Obrigado por usar o Football Chatbot! Até à próxima!")
                    break
                
                print("\n🤖 Bot:", end=" ")
                response = self.chatbot.process_question(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrompido. Até à próxima!")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                print("Tenta fazer outra pergunta ou escreve 'ajuda'.")
    
    def ask_question(self, question: str) -> str:
        """
        Fazer uma pergunta direta (para uso em scripts)
        """
        if not self.running:
            return "❌ Chatbot não está inicializado corretamente."
        
        return self.chatbot.process_question(question)

# Exemplo de uso
if __name__ == "__main__":
    # Criar interface do chatbot
    chat = FootballChatInterface()
    
    # Iniciar conversa interativa
    chat.start_chat()
    
    # Ou fazer perguntas diretas:
    # print(chat.ask_question("Como está o Benfica?"))
    # print(chat.ask_question("Classificação da Premier League"))