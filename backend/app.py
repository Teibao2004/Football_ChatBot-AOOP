from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import logging

from football_manager import FootballDataManager
from chatbot import FootballChatbot

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
CORS(app)

# Inicializar gestores
api_key = os.getenv('RAPIDAPI_KEY')
if not api_key:
    print("❌ RAPIDAPI_KEY não encontrada no arquivo .env")
    exit(1)

football_manager = FootballDataManager(api_key)
chatbot = FootballChatbot(api_key)

# Configurar Flask para UTF-8
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

@app.before_request
def before_request():
    """Middleware para garantir codificação UTF-8"""
    if request.content_type and 'application/json' in request.content_type:
        # Forçar UTF-8 para requests JSON
        request.environ['CONTENT_TYPE'] = request.content_type + '; charset=utf-8'
        logger.info(f"Request content-type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")

# Limite para season 2023 por defeito 
def get_valid_season(default=2023):
    season = request.args.get('season', type=int)
    return season if season and season <= 2023 else default

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint do chat"""
    try:
        logger.info("=== INÍCIO DO PROCESSAMENTO DO CHAT ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content-type: {request.content_type}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Log do body raw para debug
        raw_data = request.get_data()
        logger.info(f"Raw request data: {raw_data}")
        logger.info(f"Raw data length: {len(raw_data) if raw_data else 0}")
        
        # Tentar diferentes codificações
        data = None
        encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                if raw_data:
                    decoded_data = raw_data.decode(encoding)
                    logger.info(f"Decoded with {encoding}: {decoded_data}")
                    data = json.loads(decoded_data)
                    logger.info(f"Successfully parsed JSON with {encoding}")
                    break
                else:
                    data = request.get_json()
                    logger.info("Using request.get_json()")
                    break
            except UnicodeDecodeError as e:
                logger.warning(f"Failed to decode with {encoding}: {e}")
                continue
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON with {encoding}: {e}")
                continue
        
        if data is None:
            logger.error("Failed to decode request data with any encoding")
            return jsonify({'error': 'Erro ao processar dados da requisição'}), 400
        
        logger.info(f"Data parsed: {data}")
        
        question = data.get('question', '')
        league_id = data.get('league_id', None)
        logger.info(f"Pergunta recebida: '{question}'")
        logger.info(f"Pergunta length: {len(question)}")
        
        if not question:
            logger.warning("Pergunta vazia recebida")
            return jsonify({'error': 'Pergunta é obrigatória'}), 400
        
        # Processar pergunta
        logger.info("Iniciando processamento da pergunta...")
        response = chatbot.process_question(question, league_id=league_id)
        logger.info(f"Resposta gerada: {response[:100]}...")
        
        result = {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'requests_used': football_manager.requests_made
        }
        
        logger.info("=== FIM DO PROCESSAMENTO DO CHAT ===")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Erro geral no chat: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/leagues')
def get_all_leagues():
    """Obter todas as ligas disponíveis"""
    try:
        available_leagues = football_manager.get_available_leagues()
        return jsonify({
            'leagues': available_leagues,
            'requests_used': football_manager.requests_made
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leagues/<country>')
def get_leagues_by_country(country):
    """Obter ligas de um país específico"""
    try:
        leagues = football_manager.get_leagues(country)
        if leagues:
            return jsonify({
                'country': country,
                'leagues': leagues,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': f'Não foi possível obter ligas de {country}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standings/<int:league_id>')
def get_standings(league_id):
    """Obter classificação de uma liga"""
    try:
        season = get_valid_season()  # Usar função para validar season
        
        standings = football_manager.get_standings(league_id, season)
        
        if standings:
            processed_standings = []
            if standings[0].get('league', {}).get('standings'):
                table = standings[0]['league']['standings'][0]
                league_info = standings[0]['league']
                
                for team_data in table:
                    processed_standings.append({
                        'position': team_data['rank'],
                        'team': {
                            'id': team_data['team']['id'],
                            'name': team_data['team']['name'],
                            'logo': team_data['team']['logo']
                        },
                        'points': team_data['points'],
                        'played': team_data['all']['played'],
                        'won': team_data['all']['win'],
                        'drawn': team_data['all']['draw'],
                        'lost': team_data['all']['lose'],
                        'goals_for': team_data['all']['goals']['for'],
                        'goals_against': team_data['all']['goals']['against'],
                        'goal_difference': team_data['goalsDiff'],
                        'form': team_data.get('form', '')
                    })
            
            return jsonify({
                'league': {
                    'id': league_info['id'],
                    'name': league_info['name'],
                    'country': league_info['country'],
                    'season': league_info['season'],
                    'logo': league_info['logo']
                },
                'standings': processed_standings,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter classificação'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<int:team_id>/stats')
def get_team_stats(team_id):
    """Obter estatísticas de uma equipa"""
    try:
        league_id = request.args.get('league', 94, type=int)  # Default: Liga Portugal
        season = get_valid_season()  # Usar função para validar season
        
        stats = football_manager.get_team_statistics(team_id, league_id, season)
        
        if stats:
            # Processar estatísticas para resposta mais limpa
            processed_stats = {
                'team': {
                    'id': stats['team']['id'],
                    'name': stats['team']['name'],
                    'logo': stats['team']['logo']
                },
                'league': {
                    'id': stats['league']['id'],
                    'name': stats['league']['name'],
                    'season': stats['league']['season']
                },
                'fixtures': {
                    'played': stats['fixtures']['played']['total'],
                    'wins': stats['fixtures']['wins']['total'],
                    'draws': stats['fixtures']['draws']['total'],
                    'losses': stats['fixtures']['loses']['total']
                },
                'goals': {
                    'for': stats['goals']['for']['total']['total'],
                    'against': stats['goals']['against']['total']['total'],
                    'average_for': round(stats['goals']['for']['average']['total'], 2) if stats['goals']['for']['average']['total'] else 0,
                    'average_against': round(stats['goals']['against']['average']['total'], 2) if stats['goals']['against']['average']['total'] else 0
                },
                'biggest': {
                    'wins': stats['biggest']['wins'],
                    'loses': stats['biggest']['loses']
                },
                'clean_sheets': {
                    'home': stats['clean_sheet']['home'],
                    'away': stats['clean_sheet']['away'],
                    'total': stats['clean_sheet']['total']
                },
                'failed_to_score': {
                    'home': stats['failed_to_score']['home'],
                    'away': stats['failed_to_score']['away'],
                    'total': stats['failed_to_score']['total']
                }
            }
            
            return jsonify({
                'statistics': processed_stats,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter estatísticas'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/team/<int:team_id>/matches')
def get_team_matches(team_id):
    """Obter jogos recentes de uma equipa"""
    try:
        last = request.args.get('last', 5, type=int)
        matches = football_manager.get_recent_matches(team_id, last)
        
        if matches:
            # Processar jogos para resposta mais limpa
            processed_matches = []
            for match in matches:
                processed_matches.append({
                    'fixture': {
                        'id': match['fixture']['id'],
                        'date': match['fixture']['date'],
                        'status': match['fixture']['status']['long']
                    },
                    'league': {
                        'id': match['league']['id'],
                        'name': match['league']['name'],
                        'logo': match['league']['logo']
                    },
                    'teams': {
                        'home': {
                            'id': match['teams']['home']['id'],
                            'name': match['teams']['home']['name'],
                            'logo': match['teams']['home']['logo']
                        },
                        'away': {
                            'id': match['teams']['away']['id'],
                            'name': match['teams']['away']['name'],
                            'logo': match['teams']['away']['logo']
                        }
                    },
                    'goals': {
                        'home': match['goals']['home'],
                        'away': match['goals']['away']
                    },
                    'score': {
                        'halftime': match['score']['halftime'],
                        'fulltime': match['score']['fulltime']
                    }
                })
            
            return jsonify({
                'matches': processed_matches,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter jogos'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/h2h/<int:team1_id>/<int:team2_id>')
def get_head_to_head(team1_id, team2_id):
    """Obter histórico entre duas equipas"""
    try:
        h2h = football_manager.get_head_to_head(team1_id, team2_id)
        
        if h2h:
            # Processar histórico para resposta mais limpa
            processed_h2h = []
            for match in h2h:
                processed_h2h.append({
                    'fixture': {
                        'id': match['fixture']['id'],
                        'date': match['fixture']['date']
                    },
                    'league': {
                        'id': match['league']['id'],
                        'name': match['league']['name']
                    },
                    'teams': {
                        'home': {
                            'id': match['teams']['home']['id'],
                            'name': match['teams']['home']['name']
                        },
                        'away': {
                            'id': match['teams']['away']['id'],
                            'name': match['teams']['away']['name']
                        }
                    },
                    'goals': {
                        'home': match['goals']['home'],
                        'away': match['goals']['away']
                    }
                })
            
            return jsonify({
                'head_to_head': processed_h2h,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter histórico'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/league/<int:league_id>/teams')
def get_league_teams(league_id):
    """Obter equipas de uma liga"""
    try:
        season = get_valid_season()  # Usar função para validar season
        teams = football_manager.get_teams_by_league(league_id, season)
        
        if teams:
            # Processar equipas para resposta mais limpa
            processed_teams = []
            for team_data in teams:
                processed_teams.append({
                    'id': team_data['team']['id'],
                    'name': team_data['team']['name'],
                    'code': team_data['team']['code'],
                    'country': team_data['team']['country'],
                    'founded': team_data['team']['founded'],
                    'logo': team_data['team']['logo'],
                    'venue': {
                        'id': team_data['venue']['id'],
                        'name': team_data['venue']['name'],
                        'capacity': team_data['venue']['capacity']
                    }
                })
            
            return jsonify({
                'teams': processed_teams,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter equipas'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/league/<int:league_id>/topscorers')
def get_top_scorers(league_id):
    """Obter melhores marcadores de uma liga"""
    try:
        season = get_valid_season()  # Usar função para validar season
        scorers = football_manager.get_top_scorers(league_id, season)
        
        if scorers:
            # Processar marcadores para resposta mais limpa
            processed_scorers = []
            for scorer in scorers[:20]:  # Top 20
                processed_scorers.append({
                    'player': {
                        'id': scorer['player']['id'],
                        'name': scorer['player']['name'],
                        'photo': scorer['player']['photo']
                    },
                    'team': {
                        'id': scorer['statistics'][0]['team']['id'],
                        'name': scorer['statistics'][0]['team']['name'],
                        'logo': scorer['statistics'][0]['team']['logo']
                    },
                    'goals': scorer['statistics'][0]['goals']['total'],
                    'assists': scorer['statistics'][0]['goals']['assists'],
                    'games': scorer['statistics'][0]['games']['appearences']
                })
            
            return jsonify({
                'top_scorers': processed_scorers,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter marcadores'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fixtures/live')
def get_live_fixtures():
    """Obter jogos ao vivo"""
    try:
        league_id = request.args.get('league', type=int)
        fixtures = football_manager.get_live_fixtures(league_id)
        
        if fixtures is not None:
            # Processar jogos ao vivo
            processed_fixtures = []
            for fixture in fixtures:
                processed_fixtures.append({
                    'fixture': {
                        'id': fixture['fixture']['id'],
                        'date': fixture['fixture']['date'],
                        'status': fixture['fixture']['status'],
                        'elapsed': fixture['fixture']['status']['elapsed']
                    },
                    'league': {
                        'id': fixture['league']['id'],
                        'name': fixture['league']['name'],
                        'logo': fixture['league']['logo']
                    },
                    'teams': {
                        'home': {
                            'id': fixture['teams']['home']['id'],
                            'name': fixture['teams']['home']['name'],
                            'logo': fixture['teams']['home']['logo']
                        },
                        'away': {
                            'id': fixture['teams']['away']['id'],
                            'name': fixture['teams']['away']['name'],
                            'logo': fixture['teams']['away']['logo']
                        }
                    },
                    'goals': {
                        'home': fixture['goals']['home'],
                        'away': fixture['goals']['away']
                    }
                })
            
            return jsonify({
                'live_fixtures': processed_fixtures,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter jogos ao vivo'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fixtures/<date>')
def get_fixtures_by_date(date):
    """Obter jogos por data (YYYY-MM-DD)"""
    try:
        league_id = request.args.get('league', type=int)
        fixtures = football_manager.get_fixtures_by_date(date, league_id)
        
        if fixtures:
            # Processar jogos
            processed_fixtures = []
            for fixture in fixtures:
                processed_fixtures.append({
                    'fixture': {
                        'id': fixture['fixture']['id'],
                        'date': fixture['fixture']['date'],
                        'status': fixture['fixture']['status']
                    },
                    'league': {
                        'id': fixture['league']['id'],
                        'name': fixture['league']['name'],
                        'logo': fixture['league']['logo']
                    },
                    'teams': {
                        'home': {
                            'id': fixture['teams']['home']['id'],
                            'name': fixture['teams']['home']['name'],
                            'logo': fixture['teams']['home']['logo']
                        },
                        'away': {
                            'id': fixture['teams']['away']['id'],
                            'name': fixture['teams']['away']['name'],
                            'logo': fixture['teams']['away']['logo']
                        }
                    },
                    'goals': {
                        'home': fixture['goals']['home'],
                        'away': fixture['goals']['away']
                    }
                })
            
            return jsonify({
                'date': date,
                'fixtures': processed_fixtures,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': f'Não foi possível obter jogos para {date}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search/team/<team_name>')
def search_team(team_name):
    """Procurar equipa por nome"""
    try:
        teams = football_manager.search_team(team_name)
        
        if teams:
            # Processar resultados da pesquisa
            processed_teams = []
            for team_data in teams[:10]:  # Limitar a 10 resultados
                processed_teams.append({
                    'id': team_data['team']['id'],
                    'name': team_data['team']['name'],
                    'code': team_data['team']['code'],
                    'country': team_data['team']['country'],
                    'logo': team_data['team']['logo'],
                    'venue': team_data['venue']['name'] if team_data['venue'] else None
                })
            
            return jsonify({
                'search_term': team_name,
                'results': processed_teams,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': f'Não foi possível encontrar equipas com "{team_name}"'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Obter status da API"""
    try:
        cache_stats = football_manager.get_cache_stats()
        return jsonify({
            'status': 'online',
            'requests_used': football_manager.requests_made,
            'requests_remaining': 100 - football_manager.requests_made,
            'cache': cache_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Limpar cache"""
    try:
        football_manager.clear_cache()
        return jsonify({
            'message': 'Cache limpo com sucesso',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/stats')
def get_cache_stats():
    """Obter estatísticas do cache"""
    try:
        stats = football_manager.get_cache_stats()
        return jsonify({
            'cache_stats': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/popular-teams')
def get_popular_teams():
    """Obter equipas populares por liga"""
    try:
        league_id = request.args.get('league', type=int)
        
        if league_id:
            teams = football_manager.get_popular_teams_by_league(league_id)
            return jsonify({
                'league_id': league_id,
                'teams': teams
            })
        else:
            # Retornar todas as equipas populares
            all_popular_teams = {}
            for league_id, teams in football_manager.popular_teams.items():
                league_info = None
                for league_key, league_data in football_manager.available_leagues.items():
                    if league_data['id'] == league_id:
                        league_info = league_data
                        break
                
                if league_info:
                    all_popular_teams[league_info['name']] = {
                        'league_id': league_id,
                        'league_info': league_info,
                        'teams': teams
                    }
            
            return jsonify({'popular_teams': all_popular_teams})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    print("🚀 Iniciando Football ChatBot API...")
    print(f"📊 Requests disponíveis: {100 - football_manager.requests_made}/100")
    print("🏆 Ligas disponíveis:", list(football_manager.get_available_leagues().keys()))
    print("💬 Acesse: http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )