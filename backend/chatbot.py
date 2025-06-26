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
                r'standings', r'table', r'position',
                r'league table', r'league standings', r'who is first', r'leader', 
                r'top of the league', r'who is leading', r'who is on top', r'who is in first place'
            ],
            'team_stats': [
                r'estatísticas', r'stats', r'números', r'desempenho',
                r'como está', r'forma', r'rendimento', r'performance',
                r'vitórias', r'derrotas', r'empates', r'golos',
                r'statistics', r'numbers', r'performance', r'form', r'wins', 
                r'losses', r'draws', r'goals', r'record', r'results'
            ],
            'recent_matches': [
                r'últimos jogos', r'jogos recentes', r'forma recente',
                r'últimas partidas', r'últimos resultados', r'resultados recentes',
                r'recent matches', r'last games', r'latest matches', r'latest results', 
                r'recent results', r'last matches', r'recent fixtures'
            ],
            'next_matches': [
                r'próximos jogos', r'próximas partidas', r'calendário',
                r'quando joga', r'próximo jogo', r'agenda',
                r'next games', r'fixtures', r'schedule', r'upcoming matches', r'upcoming games', 
                r'next matches', r'when does.*play', r'when is.*next match', r'future games'
            ],
            'head_to_head': [
                r'vs', r'contra', r'histórico', r'confrontos',
                r'head to head', r'h2h', r'face a face', r'head-to-head', r'comparison', 
                r'compare', r'previous meetings', r'past meetings', r'previous encounters'
            ],
            'live_matches': [
                r'ao vivo', r'live', r'agora', r'jogos hoje',
                r'em direto', r'directo', r'tempo real',
                r'live matches', r'live games', r'now', r'currently playing', r'ongoing', 
                r'live scores', r'live fixtures', r'games today', r'matches today'
            ],
            'top_scorers': [
                r'melhor marcador', r'goleador', r'artilheiro',
                r'melhores marcadores', r'top scorer', r'goals',
                r'top scorers', r'best scorer', r'goal scorer', r'leading scorer', 
                r'who scored the most', r'who has most goals', r'who is top scorer'
            ],
            'league_info': [
                r'sobre a liga', r'informações da liga', r'liga',
                r'campeonato', r'torneio', r'competição',
                r'about the league', r'league info', r'competition', r'tournament', 
                r'league information', r'league details'
            ]
        }
        
        # Comandos especiais
        self.special_commands = {
            'help': ['ajuda', 'help', 'comandos', 'o que podes fazer'],
            'leagues': ['ligas', 'campeonatos', 'leagues', 'competitions'],
            'cache': ['cache', 'limpar cache', 'clear cache'],
            'stats': ['estatísticas do bot', 'stats do bot', 'info']
        }
        self.classicos = {
            94: ('benfica', 'porto'),
            140: ('real madrid', 'barcelona'),
            39: ('manchester united', 'liverpool'),
            78: ('bayern', 'dortmund'),
            135: ('inter', 'milan'),
            61: ('psg', 'marseille'),
        }
    
    def _extract_team_name(self, text: str) -> Optional[str]:
        # Tenta extrair o nome da equipa de padrões comuns, incluindo nomes compostos
        patterns = [
            r'classifica[çc][aã]o (do|da|de) ([\w\s]+?)( na tabela|$)',
            r'estat[íi]sticas (do|da|de) ([\w\s]+)',
            r'números (do|da|de) ([\w\s]+)',
            r'como est[aá] (o|a|os|as)? ([\w\s]+)',
            r'posição (do|da|de) ([\w\s]+)',
            r'últimos jogos (do|da|de) ([\w\s]+)',
            r'jogos recentes (do|da|de) ([\w\s]+)',
            r'próximos jogos (do|da|de) ([\w\s]+)',
            r'([\w\s]+) vs ([\w\s]+)',
            r'([\w\s]+) contra ([\w\s]+)',
            r'([\w\s]+) x ([\w\s]+)',
            r'desempenho (do|da|de) ([\w\s]+)',
            r'([\w\s]+) na tabela',
            r'([\w\s]+) estat[íi]sticas',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if match.lastindex:
                    for i in range(match.lastindex, 0, -1):
                        val = match.group(i)
                        if val and len(val.strip()) > 2:
                            return val.strip().replace('  ', ' ')
        return None

    def _identify_team(self, text: str, league_id: int = None) -> Optional[Dict]:
        # Primeiro tenta extrair só o nome da equipa
        team_name = self._extract_team_name(text)
        if team_name:
            team = self.data_manager.identify_team_by_name(team_name)
            # Se for lista, extrai o primeiro elemento
            if isinstance(team, list) and len(team) > 0:
                team = team[0]['team'] if 'team' in team[0] else team[0]
            if team and isinstance(team, dict):
                # Procurar a que liga pertence nos popular_teams
                for lid, teams in self.data_manager.popular_teams.items():
                    for tkey, tdata in teams.items():
                        if tdata['id'] == team['id']:
                            team['league'] = lid
                return team
        # Se não conseguiu extrair, tenta com o texto todo (fallback antigo)
        team = self.data_manager.identify_team_by_name(text)
        if isinstance(team, list) and len(team) > 0:
            team = team[0]['team'] if 'team' in team[0] else team[0]
        if team and isinstance(team, dict):
            for lid, teams in self.data_manager.popular_teams.items():
                for tkey, tdata in teams.items():
                    if tdata['id'] == team['id']:
                        team['league'] = lid
            return team
        return None

    def process_question(self, question: str, league_id: int = None) -> str:
        """
        Processar pergunta do utilizador com melhor análise contextual
        """
        question_lower = question.lower().strip()
        try:
            # Resposta especial para 'Informações sobre o chat'
            if question_lower in ["informações sobre o chat", "informacoes sobre o chat"]:
                return self._show_bot_stats()
            # Se for 'Informações sobre (team)', tratar como 'Como está o (team)'
            match = re.match(r"informações sobre (.+)", question_lower)
            if match and match.group(1).strip() != "o chat":
                team = match.group(1).strip()
                return self.process_question(f"Como está o {team}")
            # Clássico dinâmico
            if 'clássico' in question_lower or 'classico' in question_lower:
                league_info = self._identify_league(question_lower)
                if league_info and 'id' in league_info:
                    lid = league_info['id']
                else:
                    lid = 94  # Default para Portugal
                team1_slug, team2_slug = self.classicos.get(lid, ('benfica', 'porto'))
                team1 = self.data_manager.identify_team_by_name(team1_slug)
                team2 = self.data_manager.identify_team_by_name(team2_slug)
                if team1 and isinstance(team1, list) and len(team1) > 0:
                    team1 = team1[0]['team'] if 'team' in team1[0] else team1[0]
                else:
                    team1 = None
                if team2 and isinstance(team2, list) and len(team2) > 0:
                    team2 = team2[0]['team'] if 'team' in team2[0] else team2[0]
                else:
                    team2 = None
                if team1 and team2:
                    h2h = self.data_manager.get_head_to_head(team1['id'], team2['id'])
                    if h2h and len(h2h) > 0:
                        match = h2h[0]
                        home = match['teams']['home']['name']
                        away = match['teams']['away']['name']
                        home_goals = match['goals']['home']
                        away_goals = match['goals']['away']
                        date = match['fixture']['date'][:10]
                        response = f"🔥 **Clássico {home} vs {away}** 🔥\n\nÚltimo jogo: {date}\n{home} {home_goals} - {away_goals} {away}\n"
                        if len(h2h) > 1:
                            response += "\nHistórico recente:\n"
                            for m in h2h[:5]:
                                d = m['fixture']['date'][:10]
                                h = m['teams']['home']['name']
                                a = m['teams']['away']['name']
                                hg = m['goals']['home']
                                ag = m['goals']['away']
                                response += f"- {d}: {h} {hg}-{ag} {a}\n"
                        response += "\nQueres saber mais estatísticas ou o histórico completo? Pergunta!"
                        return response
                    else:
                        return "🔥 **Clássico** 🔥\n\nNão há jogos recentes nem histórico disponível entre estas equipas. Queres saber estatísticas ou próximos jogos? Pergunta!"
                return "🔥 **Clássico** 🔥\n\nNão foi possível identificar as equipas do clássico nesta liga."
            # Pergunta combinada: posição + estatísticas
            if (("posição" in question_lower or "posicao" in question_lower or "tabela" in question_lower) and "estat" in question_lower):
                league_info = self._identify_league(question_lower)
                if league_id is not None:
                    league_info = self.data_manager.get_league_info(int(league_id)) or {}
                league_id_val = league_info['id'] if isinstance(league_info, dict) and 'id' in league_info else 94
                if league_id_val is None:
                    league_id_val = 94
                team_info = self._identify_team(question_lower, league_id_val)
                if not team_info:
                    return "🤔 Desculpa, não percebi a equipa. Escreve 'ajuda' para ver exemplos de perguntas."
                standings_resp = self._handle_standings(question_lower, league_info if league_info is not None else {}, team_info)
                stats_resp = self._handle_team_stats(question_lower, team_info, league_info if league_info is not None else {})
                return standings_resp + "\n\n" + stats_resp
            # Verificar comandos especiais primeiro
            special_response = self._handle_special_commands(question_lower)
            if special_response:
                return special_response
            # Identificar tipo de pergunta
            question_type = self._classify_question(question_lower)
            # Identificar liga e equipa no contexto
            league_info = self._identify_league(question_lower)
            league_id_val = league_info['id'] if isinstance(league_info, dict) and 'id' in league_info and league_info['id'] is not None else 94
            team_info = self._identify_team(question_lower, league_id_val)
            # Se não encontrou equipa e a pergunta é sobre equipa, devolve mensagem amigável
            if question_type in ['team_stats', 'recent_matches', 'next_matches'] and not team_info:
                return "🤔 Desculpa, não percebi a equipa. Escreve 'ajuda' para ver exemplos de perguntas."
            # Processar baseado no tipo
            if question_type == 'standings':
                return self._handle_standings(question_lower, league_info if league_info is not None else {}, team_info if team_info is not None else {})
            elif question_type == 'team_stats':
                return self._handle_team_stats(question_lower, team_info if team_info is not None else {}, league_info if league_info is not None else {})
            elif question_type == 'recent_matches':
                return self._handle_recent_matches(question_lower, team_info if team_info is not None else {}, league_info if league_info is not None else {})
            elif question_type == 'next_matches':
                return self._handle_next_matches(question_lower, team_info if team_info is not None else {}, league_info if league_info is not None else {})
            elif question_type == 'head_to_head':
                return self._handle_head_to_head(question_lower)
            elif question_type == 'top_scorers':
                return self._handle_top_scorers(question_lower, league_info if league_info is not None else {})
            elif question_type == 'league_info':
                return self._handle_league_info(question_lower, league_info if league_info is not None else {})
            else:
                return self._handle_general(question_lower, team_info if team_info is not None else {}, league_info if league_info is not None else {})
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
        
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'general'
    
    def _identify_league(self, text: str) -> Optional[Dict]:
        """
        Identificar liga no texto
        """
        return self.data_manager.identify_league_by_name(text)
    
    def _handle_standings(self, question: str, league_info: dict = None, team_info: dict = None) -> str:
        league_info = league_info or {}
        team_info = team_info or {}
        league_id = league_info.get('id', 94)
        league_name = league_info.get('name', 'Liga Portugal')
        league_flag = league_info.get('flag', '🇵🇹')
        standings = self.data_manager.get_standings(league_id, 2023)
        if not standings:
            return f"😔 Não consegui obter a classificação da {league_name} no momento. Tenta novamente mais tarde."
        table = standings[0]['league']['standings'][0]
        # Se pergunta sobre líder
        if any(word in question for word in ['líder', 'lider', 'primeiro lugar', 'quem está em primeiro']):
            leader = table[0]
            pos = leader['rank']
            name = leader['team']['name']
            points = leader['points']
            played = leader['all']['played']
            return f"🥇 **Líder da {league_name}:**\n\n<b>{pos}. {name}</b> - {points} pts ({played}j)"
        # Se pergunta específica sobre uma equipa
        highlight_team = team_info.get('id') if team_info else None
        highlight_names = set()
        if team_info and team_info.get('name'):
            # Adiciona variantes do nome para comparação robusta
            highlight_names.add(team_info['name'].lower())
            # Adiciona variantes conhecidas se existirem
            league_id_val = league_info['id'] if isinstance(league_info, dict) and 'id' in league_info else 94
            popular_teams = self.data_manager.popular_teams.get(league_id_val, {})
            for team_key, team_data in popular_teams.items():
                if team_data['id'] == highlight_team:
                    for n in team_data['names']:
                        highlight_names.add(n.lower())
        response = f"{league_flag} **Classificação da {league_name}:**\n\n"
        display_rows = []
        for i, team_data in enumerate(table):
            pos = team_data['rank']
            name = team_data['team']['name']
            points = team_data['points']
            played = team_data['all']['played']
            # Destacar só o nome da equipa a bold
            if highlight_team and team_data['team']['id'] == highlight_team:
                name_disp = f"**{name}**"
            elif highlight_names and name.lower() in highlight_names:
                name_disp = f"**{name}**"
            else:
                name_disp = name
            row = f"{pos}. {name_disp} - {points} pts ({played}j)"
            display_rows.append(row)
        # Mostrar top 10, mas garantir que equipa pedida aparece
        highlight_row = None
        for row in display_rows:
            if '**' in row:
                highlight_row = row
                break
        if highlight_row and highlight_row not in display_rows[:10]:
            response += '\n'.join(display_rows[:9] + [highlight_row])
        else:
            response += '\n'.join(display_rows[:10])
        if len(table) > 10:
            response += f"\n\n... e mais {len(table)-10} equipas"
        return response
    
    def _handle_team_stats(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre estatísticas de equipas
        """
        team_info = team_info or {}
        league_info = league_info or {}
        if not team_info:
            return "🤔 De que equipa queres saber as estatísticas? Especifica, por favor."
        
        team_id = team_info['id']
        team_name = team_info.get('name', 'equipa').title()
        league_id = team_info.get('league', 94)  # Default: Liga Portugal
        
        stats = self.data_manager.get_team_statistics(team_id, league_id, 2023)
        
        if not stats:
            return f"😔 Não consegui obter as estatísticas do {team_name} no momento."
        
        try:
            # Extrair dados das estatísticas
            team_data = stats.get('team', {})
            league_data = stats.get('league', {})
            fixtures_data = stats.get('fixtures', {})
            goals_data = stats.get('goals', {})
            
            # Verificar se os dados necessários existem
            if not fixtures_data or not goals_data:
                return f"😔 Dados incompletos para {team_name}. Tenta novamente mais tarde."
            
            # Calcular estatísticas
            played = fixtures_data.get('played', {}).get('total', 0)
            wins = fixtures_data.get('wins', {}).get('total', 0)
            draws = fixtures_data.get('draws', {}).get('total', 0)
            losses = fixtures_data.get('loses', {}).get('total', 0)
            
            goals_for = goals_data.get('for', {}).get('total', {}).get('total', 0)
            goals_against = goals_data.get('against', {}).get('total', {}).get('total', 0)
            
            # Calcular percentagens
            win_rate = (wins / played * 100) if played > 0 else 0
            draw_rate = (draws / played * 100) if played > 0 else 0
            loss_rate = (losses / played * 100) if played > 0 else 0
            
            # Calcular média de golos
            avg_goals_for = round(goals_for / played, 2) if played > 0 else 0
            avg_goals_against = round(goals_against / played, 2) if played > 0 else 0
            
            response = f"📊 **Estatísticas do {team_name}:**\n\n"
            response += f"🏟️ **Jogos:** {played}\n"
            response += f"✅ **Vitórias:** {wins} ({win_rate:.1f}%)\n"
            response += f"⚖️ **Empates:** {draws} ({draw_rate:.1f}%)\n"
            response += f"❌ **Derrotas:** {losses} ({loss_rate:.1f}%)\n\n"
            response += f"⚽ **Golos:** {goals_for} marcados, {goals_against} sofridos\n"
            response += f"📈 **Média:** {avg_goals_for} por jogo marcados, {avg_goals_against} por jogo sofridos\n"
            
            # Adicionar informações da liga se disponível
            if league_data:
                league_name = league_data.get('name', 'Liga')
                season = league_data.get('season', '2024')
                response += f"\n🏆 **Liga:** {league_name} ({season})"
            
            return response
            
        except Exception as e:
            return f"😔 Erro ao processar as estatísticas do {team_name}. Tenta novamente."
    
    def _handle_recent_matches(self, question: str, team_info: Dict = None, league_info: Dict = None) -> str:
        """
        Responder perguntas sobre jogos recentes
        """
        team_info = team_info or {}
        league_info = league_info or {}
        print(f"[DEBUG] team_info: {team_info}")  # Debug
        if not team_info and not league_info:
            return "🤔 De que equipa ou liga queres saber os últimos jogos?"
        
        if team_info:
            team_id = team_info.get('id')
            team_name = team_info.get('name', 'equipa').title()
            print(f"[DEBUG] team_id: {team_id}, team_name: {team_name}")  # Debug
            
            matches = self.data_manager.get_recent_matches(team_id, 5)
            print(f"[DEBUG] matches: {matches}")  # Debug
            
            if not matches:
                return f"😔 Não consegui obter os últimos jogos do {team_name}."
            
            response = f"📅 **Últimos 5 jogos do {team_name}:**\n\n"
            
            for i, match in enumerate(matches[:5]):
                
                try:
                    home_team = match['teams']['home']['name']
                    away_team = match['teams']['away']['name']
                    home_goals = match['goals']['home'] if match['goals']['home'] is not None else 0
                    away_goals = match['goals']['away'] if match['goals']['away'] is not None else 0
                    date = match['fixture']['date'][:10]
                    status = match['fixture']['status']['short']
                    
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
                    
                except Exception as e:
                    print(f"[DEBUG] Exception in match loop: {e}")  # Debug
                    continue
            
            return response
            
        else:
            # Jogos recentes de uma liga
            league_id = league_info['id']
            league_name = league_info['name']
            
            matches = self.data_manager.get_fixtures_by_league(league_id, 2023, 10)
            
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
        team_info = team_info or {}
        league_info = league_info or {}
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
                # Se for lista, extrai o primeiro elemento
                if isinstance(team, list) and len(team) > 0:
                    team = team[0]['team'] if 'team' in team[0] else team[0]
                if isinstance(team, dict):
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
                    # Se for lista, extrai o primeiro elemento
                    if isinstance(team1, list) and len(team1) > 0:
                        team1 = team1[0]['team'] if 'team' in team1[0] else team1[0]
                    if isinstance(team2, list) and len(team2) > 0:
                        team2 = team2[0]['team'] if 'team' in team2[0] else team2[0]
                    if team1 and team2 and isinstance(team1, dict) and isinstance(team2, dict):
                        teams_found = [team1, team2]
                        break
        
        if len(teams_found) < 2:
            return "🤔 Preciso de duas equipas para mostrar o histórico. Ex: 'Benfica vs Porto' ou 'Real Madrid contra Barcelona'"
        
        team1 = teams_found[0]
        team2 = teams_found[1]
        
        h2h = self.data_manager.get_head_to_head(team1['id'], team2['id'])
        if not h2h:
            return f"😔 Não consegui obter o histórico entre {team1['name']} e {team2['name']}."
        
        team1_name = team1['name'] if isinstance(team1['name'], str) else str(team1['name']).title()
        team2_name = team2['name'] if isinstance(team2['name'], str) else str(team2['name']).title()
        
        response = f"⚔️ **{team1_name} vs {team2_name}** (Últimos confrontos):\n\n"
        
        team1_wins = 0
        team2_wins = 0
        draws = 0;
        
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
        
        top_scorers = self.data_manager.get_top_scorers(league_id, 2023)
        
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
        standings = self.data_manager.get_standings(league_info['id'], 2023)
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
        team_info = team_info or {}
        league_info = league_info or {}
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