import requests
import json
import time
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Carregar variáveis do arquivo .env
load_dotenv()

class FootballDataManager:
    
    def __init__(self, api_key: str = None):
        # Se não for fornecida uma API key, buscar do .env
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API key não encontrada. Defina RAPIDAPI_KEY no arquivo .env ou passe como parâmetro.")
        
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        self.cache = {}
        self.requests_made = 0
        self.last_request_time = None
        
        # Buscar configurações do .env
        self.cache_duration = int(os.getenv('CACHE_DURATION', 6))  # Default: 6 horas
        
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Faz request à API com rate limiting e cache
        """
        # Rate limiting: máximo 30 requests por minuto
        if self.last_request_time:
            time_diff = time.time() - self.last_request_time
            if time_diff < 2:  # Esperar 2 segundos entre requests
                time.sleep(2 - time_diff)
        
        # Verificar limite diário
        if self.requests_made >= 100:
            print("❌ Limite diário de requests atingido (100/dia)")
            return None
            
        # Criar chave de cache
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True) if params else ''}"
        
        # Verificar cache
        if cache_key in self.cache:
            cache_data = self.cache[cache_key]
            if datetime.now() < cache_data['expires']:
                print(f"✅ Cache hit para {endpoint}")
                return cache_data['data']
        
        # Fazer request
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            self.requests_made += 1
            self.last_request_time = time.time()
            
            print(f"📡 Request {self.requests_made}/100: {endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Cache pela duração definida no .env
                self.cache[cache_key] = {
                    'data': data,
                    'expires': datetime.now() + timedelta(hours=self.cache_duration)
                }
                
                return data
            else:
                print(f"❌ Erro {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro na request: {e}")
            return None
    
    def get_leagues(self, country: str = "Portugal") -> Optional[List[Dict]]:
        """
        Obter ligas de um país
        """
        params = {"country": country}
        data = self._make_request("leagues", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_standings(self, league_id: int, season: int = 2024) -> Optional[List[Dict]]:
        """
        Obter classificação de uma liga
        """
        params = {"league": league_id, "season": season}
        data = self._make_request("standings", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_team_statistics(self, team_id: int, league_id: int, season: int = 2024) -> Optional[Dict]:
        """
        Obter estatísticas de uma equipa
        """
        params = {"team": team_id, "league": league_id, "season": season}
        data = self._make_request("teams/statistics", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_recent_matches(self, team_id: int, last: int = 5) -> Optional[List[Dict]]:
        """
        Obter últimos jogos de uma equipa
        """
        params = {"team": team_id, "last": last}
        data = self._make_request("fixtures", params)
        
        if data and data.get('response'):
            return data['response']
        return None
    
    def get_head_to_head(self, team1_id: int, team2_id: int) -> Optional[List[Dict]]:
        """
        Obter histórico entre duas equipas
        """
        params = {"h2h": f"{team1_id}-{team2_id}"}
        data = self._make_request("fixtures/headtohead", params)
        
        if data and data.get('response'):
            return data['response']
        return None

# Exemplo de uso
if __name__ == "__main__":
    # Agora pode ser usado sem passar a API key
    football_manager = FootballDataManager()
    
    # Ou ainda pode passar a API key manualmente se necessário
    # football_manager = FootballDataManager("sua_api_key_aqui")