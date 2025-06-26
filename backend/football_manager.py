import requests
import json
import time
import logging
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Configurar logging
logger = logging.getLogger(__name__)

# Carregar variáveis do arquivo .env
load_dotenv()

class FootballDataManager:
    
    def __init__(self, api_key: str = None):
        # Se não for fornecida uma API key, buscar do .env
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API key não encontrada. Defina RAPIDAPI_KEY no arquivo .env ou passe como parâmetro.")
        
        # URL correta para API-Sports (API-Football)
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "x-apisports-key": self.api_key
        }
        self.cache = {}
        self.requests_made = 0  # Reset para permitir mais testes
        self.last_request_time = None
        
        # Buscar configurações do .env
        self.cache_duration = int(os.getenv('CACHE_DURATION', 6))  # Default: 6 horas
        
        logger.info(f"FootballDataManager inicializado com API key: {self.api_key[:10]}...")
        
        # Ligas disponíveis com IDs corretos para API-Sports
        self.available_leagues = {
            'portugal': {'id': 94, 'name': 'Primeira Liga', 'country': 'Portugal', 'flag': '🇵🇹'},
            'england': {'id': 39, 'name': 'Premier League', 'country': 'England', 'flag': '🏴󠁧󠁢󠁥󠁮󠁧󠁿'},
            'spain': {'id': 140, 'name': 'La Liga', 'country': 'Spain', 'flag': '🇪🇸'},
            'germany': {'id': 78, 'name': 'Bundesliga', 'country': 'Germany', 'flag': '🇩🇪'},
            'italy': {'id': 135, 'name': 'Serie A', 'country': 'Italy', 'flag': '🇮🇹'},
            'france': {'id': 61, 'name': 'Ligue 1', 'country': 'France', 'flag': '🇫🇷'},
            'netherlands': {'id': 88, 'name': 'Eredivisie', 'country': 'Netherlands', 'flag': '🇳🇱'},
            'brazil': {'id': 71, 'name': 'Série A', 'country': 'Brazil', 'flag': '🇧🇷'},
            'argentina': {'id': 128, 'name': 'Liga Profesional', 'country': 'Argentina', 'flag': '🇦🇷'},
            'champions': {'id': 2, 'name': 'Champions League', 'country': 'World', 'flag': '🏆'},
            'europa': {'id': 3, 'name': 'Europa League', 'country': 'World', 'flag': '🏆'},
            'conference': {'id': 848, 'name': 'Conference League', 'country': 'World', 'flag': '🏆'}
        }
        
        # Equipas populares por liga
        self.popular_teams = {
            94: {  # Primeira Liga
                'benfica': {'id': 211, 'names': ['benfica', 'slb', 'águias', 'encarnados']},
                'porto': {'id': 212, 'names': ['porto', 'fcp', 'dragões', 'azuis e brancos']},
                'sporting': {'id': 228, 'names': ['sporting', 'scp', 'leões', 'verdes e brancos']},
                'braga': {'id': 227, 'names': ['braga', 'sc braga', 'minhotos', 'marroquinos']},
                'vitoria': {'id': 230, 'names': ['vitória', 'vitoria', 'guimaraes', 'vitória guimarães', 'vitoria guimaraes', 'vsc', 'vitoria sc', 'guimarães']},
                'boavista': {'id': 218, 'names': ['boavista', 'boavista fc', 'axadrezados']},
                'gil_vicente': {'id': 219, 'names': ['gil vicente', 'gil', 'gvfc', 'galos']},
                'famalicao': {'id': 229, 'names': ['famalicão', 'famalicao', 'fc famalicão', 'fc famalicao']},
                'moreirense': {'id': 226, 'names': ['moreirense', 'moreirense fc']},
                'rio_ave': {'id': 231, 'names': ['rio ave', 'rio ave fc']}
            },
            39: {  # Premier League
                'manchester_united': {'id': 33, 'names': ['manchester united', 'man utd', 'united', 'red devils']},
                'manchester_city': {'id': 50, 'names': ['manchester city', 'man city', 'city', 'citizens']},
                'liverpool': {'id': 40, 'names': ['liverpool', 'reds', 'lfc']},
                'arsenal': {'id': 42, 'names': ['arsenal', 'gunners', 'afc']},
                'chelsea': {'id': 49, 'names': ['chelsea', 'blues', 'cfc']},
                'tottenham': {'id': 47, 'names': ['tottenham', 'spurs', 'thfc']},
                'newcastle': {'id': 34, 'names': ['newcastle', 'newcastle united', 'magpies']},
                'west_ham': {'id': 48, 'names': ['west ham', 'west ham united', 'hammers']},
                'aston_villa': {'id': 66, 'names': ['aston villa', 'villa', 'avfc']},
                'brighton': {'id': 51, 'names': ['brighton', 'brighton & hove albion', 'seagulls']}
            },
            140: {  # La Liga
                'real_madrid': {'id': 541, 'names': ['real madrid', 'madrid', 'real', 'merengues']},
                'barcelona': {'id': 529, 'names': ['barcelona', 'barça', 'barca', 'blaugrana']},
                'atletico': {'id': 530, 'names': ['atletico madrid', 'atletico', 'atleti', 'colchoneros']},
                'sevilla': {'id': 536, 'names': ['sevilla', 'sevilla fc']},
                'valencia': {'id': 532, 'names': ['valencia', 'valencia cf', 'che']},
                'villarreal': {'id': 533, 'names': ['villarreal', 'villarreal cf', 'yellow submarine']},
                'real_sociedad': {'id': 548, 'names': ['real sociedad', 'sociedad', 'txuri-urdin']},
                'athletic': {'id': 531, 'names': ['athletic bilbao', 'athletic', 'lions']}
            },
            78: {  # Bundesliga
                'bayern': {'id': 157, 'names': ['bayern munich', 'bayern', 'fcb', 'bavarians']},
                'dortmund': {'id': 165, 'names': ['borussia dortmund', 'dortmund', 'bvb', 'black and yellow']},
                'leipzig': {'id': 173, 'names': ['rb leipzig', 'leipzig', 'red bulls']},
                'leverkusen': {'id': 168, 'names': ['bayer leverkusen', 'leverkusen', 'werkself']},
                'frankfurt': {'id': 169, 'names': ['eintracht frankfurt', 'frankfurt', 'eagles']},
                'wolfsburg': {'id': 170, 'names': ['vfl wolfsburg', 'wolfsburg', 'wolves']},
                'gladbach': {'id': 163, 'names': ['borussia monchengladbach', 'gladbach', 'bmg']},
                'stuttgart': {'id': 172, 'names': ['vfb stuttgart', 'stuttgart']}
            },
            135: {  # Serie A
                'juventus': {'id': 496, 'names': ['juventus', 'juve', 'bianconeri', 'old lady']},
                'inter': {'id': 505, 'names': ['inter milan', 'inter', 'nerazzurri']},
                'milan': {'id': 489, 'names': ['ac milan', 'milan', 'rossoneri']},
                'napoli': {'id': 492, 'names': ['napoli', 'partenopei', 'azzurri']},
                'roma': {'id': 497, 'names': ['as roma', 'roma', 'giallorossi']},
                'lazio': {'id': 487, 'names': ['lazio', 'ss lazio', 'biancocelesti']},
                'fiorentina': {'id': 502, 'names': ['fiorentina', 'viola', 'acf fiorentina']},
                'atalanta': {'id': 499, 'names': ['atalanta', 'atalanta bc', 'nerazzurri']}
            },
            61: {  # Ligue 1
                'psg': {'id': 85, 'names': ['psg', 'paris saint germain', 'paris', 'parisiens']},
                'marseille': {'id': 81, 'names': ['marseille', 'om', 'olympique marseille']},
                'lyon': {'id': 80, 'names': ['lyon', 'ol', 'olympique lyonnais']},
                'monaco': {'id': 91, 'names': ['monaco', 'as monaco', 'monegasques']},
                'lille': {'id': 79, 'names': ['lille', 'losc', 'lille osc']},
                'nice': {'id': 108, 'names': ['nice', 'ogc nice']},
                'rennes': {'id': 111, 'names': ['rennes', 'stade rennais']},
                'montpellier': {'id': 82, 'names': ['montpellier', 'mhsc']}
            }
        }
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Faz request à API com rate limiting e cache
        """
        logger.info(f"=== FAZENDO REQUEST: {endpoint} ===")
        logger.info(f"Parâmetros: {params}")
        
        # Rate limiting: máximo 30 requests por minuto
        if self.last_request_time:
            time_diff = time.time() - self.last_request_time
            if time_diff < 2:  # Esperar 2 segundos entre requests
                logger.info(f"Aguardando {2 - time_diff:.2f}s para rate limiting...")
                time.sleep(2 - time_diff)
        
        # Verificar limite diário
        if self.requests_made >= 100:
            logger.error("❌ Limite diário de requests atingido (100/dia)")
            return None
            
        # Criar chave de cache
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
        
        # Verificar cache
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now() < cache_data['expires']:
                logger.info(f"✅ Cache hit para {endpoint}")
                return cache_data['data']
        
        # Fazer request
        url = f"{self.base_url}/{endpoint}"
        try:
            logger.info(f"📡 Request {self.requests_made + 1}/100: {url}")
            logger.info(f"Headers: {self.headers}")
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            self.requests_made += 1
            self.last_request_time = time.time()
            
            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Verificar se a resposta contém dados válidos
                if data.get('response') is not None:
                    # Cache pela duração definida no .env
                    self.cache[cache_key] = {
                        'data': data,
                        'expires': datetime.now() + timedelta(hours=self.cache_duration)
                    }
                    logger.info(f"✅ Request bem-sucedida para {endpoint}")
                    return data
                else:
                    logger.warning(f"⚠️ Resposta vazia para {endpoint}")
                    logger.warning(f"Response content: {response.text[:200]}...")
                    return None
            elif response.status_code == 429:
                logger.error("❌ Rate limit atingido. Aguardando...")
                time.sleep(60)  # Esperar 1 minuto
                return self._make_request(endpoint, params)  # Tentar novamente
            else:
                logger.error(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ Timeout na request para {endpoint}")
            return None
        except Exception as e:
            logger.error(f"❌ Erro na request: {e}", exc_info=True)
            return None
    
    def get_available_leagues(self) -> Dict:
        """
        Retornar ligas disponíveis
        """
        return self.available_leagues
    
    def get_popular_teams_by_league(self, league_id: int) -> Dict:
        """
        Retornar equipas populares de uma liga
        """
        return self.popular_teams.get(league_id, {})
    
    def get_leagues(self, country: str = "Portugal") -> Optional[List[Dict]]:
        """
        Obter ligas de um país
        """
        params = {"country": country}
        data = self._make_request("leagues", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_standings(self, league_id: int, season: int = 2023) -> Optional[List[Dict]]:
        """
        Obter classificação de uma liga
        """
        params = {"league": league_id, "season": season}
        data = self._make_request("standings", params)
        if data and data.get('response') and len(data['response']) > 0:
            return data['response']
        return None
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int = 2023) -> Optional[Dict]:
        """
        Obter estatísticas de uma equipa
        """
        params = {"team": team_id, "league": league_id, "season": season}
        data = self._make_request("teams/statistics", params)
        print(f"DEBUG: get_team_statistics para team_id={team_id}, league_id={league_id}, season={season}")
        print(f"DEBUG: Resposta da API: {data}")
        if data and data.get('response') and len(data['response']) > 0:
            return data['response']
        return None
    
    def get_recent_matches(self, team_id: int, last: int = 5) -> Optional[List[Dict]]:
        """
        Obter últimos jogos de uma equipa usando datas (compatível com plano gratuito)
        """
        from datetime import datetime, timedelta
        
        # Calcular datas dos últimos 30 dias
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        params = {
            "team": team_id, 
            "season": 2023,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d")
        }
        data = self._make_request("fixtures", params)
        print(f"DEBUG: get_recent_matches para team_id={team_id}")
        print(f"DEBUG: Resposta da API: {data}")
        if data and data.get('response') and len(data['response']) > 0:
            # Ordenar por data e pegar os últimos 5
            fixtures = sorted(data['response'], key=lambda x: x['fixture']['date'], reverse=True)
            return fixtures[:last]
        return None
    
    def get_fixtures_by_league(self, league_id: int, season: int = 2023, last: int = 10) -> Optional[List[Dict]]:
        """
        Obter últimos jogos de uma liga
        """
        params = {"league": league_id, "season": season, "last": last}
        data = self._make_request("fixtures", params)
        if data and data.get('response') and len(data['response']) > 0:
            return data['response']
        return None
    
    def get_head_to_head(self, team1_id: int, team2_id: int, last: int = None) -> Optional[List[Dict]]:
        """
        Obter histórico entre duas equipas (sem season, histórico completo)
        """
        params = {"h2h": f"{team1_id}-{team2_id}"}
        if last is not None:
            params["last"] = str(last)
        data = self._make_request("fixtures/headtohead", params)
        if data and data.get('response') and len(data['response']) > 0:
            return data['response']
        return None
    
    def get_teams_by_league(self, league_id: int, season: int = 2024) -> Optional[List[Dict]]:
        """
        Obter equipas de uma liga
        """
        params = {"league": league_id, "season": season}
        data = self._make_request("teams", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_top_scorers(self, league_id: int, season: int = 2023) -> Optional[List[Dict]]:
        """
        Obter melhores marcadores de uma liga
        """
        params = {"league": league_id, "season": season}
        data = self._make_request("players/topscorers", params)
        if data and data.get('response') and len(data['response']) > 0:
            return data['response']
        return None
    
    def search_team(self, team_name: str) -> Optional[List[Dict]]:
        """
        Procurar equipa por nome
        """
        params = {"search": team_name}
        data = self._make_request("teams", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_live_fixtures(self, league_id: int = None) -> Optional[List[Dict]]:
        """
        Obter jogos ao vivo
        """
        params = {"live": "all"}
        if league_id:
            params["league"] = league_id
            
        data = self._make_request("fixtures", params)
        
        if data and data.get('response'):
            return data['response']
        return []  # Retornar lista vazia se não houver jogos ao vivo
    
    def get_fixtures_by_date(self, date: str, league_id: int = None) -> Optional[List[Dict]]:
        """
        Obter jogos por data (formato: YYYY-MM-DD)
        """
        params = {"date": date}
        if league_id:
            params["league"] = league_id
            
        data = self._make_request("fixtures", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_next_fixtures(self, team_id: int = None, league_id: int = None, next: int = 5) -> Optional[List[Dict]]:
        """
        Obter próximos jogos
        """
        params = {"next": next}
        if team_id:
            params["team"] = team_id
        if league_id:
            params["league"] = league_id
            
        data = self._make_request("fixtures", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def identify_team_by_name(self, team_name: str) -> Optional[List[Dict]]:
        """
        Procurar equipa por nome
        """
        params = {"search": team_name}
        data = self._make_request("teams", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def identify_league_by_name(self, league_name: str) -> Optional[Dict]:
        """
        Identificar liga por nome
        """
        league_name_lower = league_name.lower()
        
        # Mapeamento de nomes alternativos
        league_aliases = {
            'premier': 'england',
            'premier league': 'england',
            'pl': 'england',
            'epl': 'england',
            'bundesliga': 'germany',
            'buli': 'germany',
            'serie a': 'italy',
            'seria a': 'italy',
            'la liga': 'spain',
            'laliga': 'spain',
            'ligue 1': 'france',
            'ligue1': 'france',
            'primeira liga': 'portugal',
            'liga portugal': 'portugal',
            'liga nos': 'portugal',
            'eredivisie': 'netherlands',
            'champions': 'champions',
            'ucl': 'champions',
            'europa league': 'europa',
            'uel': 'europa',
            'conference': 'conference',
            'uecl': 'conference'
        }
        
        # Verificar aliases
        for alias, league_key in league_aliases.items():
            if alias in league_name_lower:
                return self.available_leagues.get(league_key)
        
        # Verificar nomes diretos
        for league_key, league_info in self.available_leagues.items():
            if league_key in league_name_lower or league_info['name'].lower() in league_name_lower:
                return league_info
        
        return None
    
    def get_league_info(self, league_id: int) -> Optional[Dict]:
        """
        Obter informações de uma liga pelo ID
        """
        for league_key, league_info in self.available_leagues.items():
            if league_info['id'] == league_id:
                return league_info
        return None
    
    def get_team_info(self, team_id: int) -> Optional[Dict]:
        """
        Obter informações básicas de uma equipa
        """
        params = {"id": team_id}
        data = self._make_request("teams", params)
        
        if data and data.get('response') and len(data['response']) > 0:
            return data['response'][0]
        return None
    
    def clear_cache(self):
        """
        Limpar cache
        """
        self.cache.clear()
        print("🗑️ Cache limpo!")
    
    def get_cache_stats(self) -> Dict:
        """
        Obter estatísticas do cache
        """
        total_entries = len(self.cache)
        expired_entries = 0
        
        for entry in self.cache.values():
            if datetime.now() > entry['expires']:
                expired_entries += 1
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'requests_made': self.requests_made,
            'requests_remaining': 100 - self.requests_made
        }

# Exemplo de uso
if __name__ == "__main__":
    # Agora pode ser usado sem passar a API key
    football_manager = FootballDataManager()
    
    # Testar ligas disponíveis
    print("Ligas disponíveis:", list(football_manager.get_available_leagues().keys()))
    
    # Testar identificação de equipa
    team = football_manager.identify_team_by_name("benfica")
    print("Equipa encontrada:", team)
    
    # Testar estatísticas do cache
    print("Estatísticas do cache:", football_manager.get_cache_stats())