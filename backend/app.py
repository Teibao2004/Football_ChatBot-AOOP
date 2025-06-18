from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import json
from datetime import datetime

from football_manager import FootballDataManager
from chatbot import FootballChatbot

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

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint do chat"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({'error': 'Pergunta é obrigatória'}), 400
        
        # Processar pergunta
        response = chatbot.process_question(question)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'requests_used': football_manager.requests_made
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leagues')
def get_leagues():
    """Obter ligas disponíveis"""
    try:
        leagues = football_manager.get_leagues("Portugal")
        if leagues:
            return jsonify({
                'leagues': leagues,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter ligas'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/standings/<int:league_id>')
def get_standings(league_id):
    """Obter classificação de uma liga"""
    try:
        season = request.args.get('season', 2024, type=int)
        standings = football_manager.get_standings(league_id, season)
        
        if standings:
            return jsonify({
                'standings': standings,
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
        season = request.args.get('season', 2024, type=int)
        
        stats = football_manager.get_team_statistics(team_id, league_id, season)
        
        if stats:
            return jsonify({
                'statistics': stats,
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
            return jsonify({
                'matches': matches,
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
            return jsonify({
                'head_to_head': h2h,
                'requests_used': football_manager.requests_made
            })
        else:
            return jsonify({'error': 'Não foi possível obter histórico'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def get_status():
    """Status da API e requests utilizados"""
    return jsonify({
        'status': 'online',
        'requests_used': football_manager.requests_made,
        'requests_limit': 100,
        'cache_entries': len(football_manager.cache),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/popular-teams')
def get_popular_teams():
    """Obter equipas populares portuguesas"""
    teams = [
        {'id': 211, 'name': 'Benfica', 'league': 94},
        {'id': 212, 'name': 'Porto', 'league': 94},
        {'id': 228, 'name': 'Sporting CP', 'league': 94},
        {'id': 230, 'name': 'Vitória SC', 'league': 94},
        {'id': 227, 'name': 'SC Braga', 'league': 94}
    ]
    
    return jsonify({'teams': teams})

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    print("🚀 Iniciando Football ChatBot API...")
    print(f"📊 Requests disponíveis: {100 - football_manager.requests_made}/100")
    print("💬 Acesse: http://localhost:5000")
    
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )