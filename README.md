# Thorp: Your Crypto Investment Advisor
![Home](https://github.com/user-attachments/assets/d73a1970-0b61-4660-834d-0d0b7051d6c5)

## Brief
Thorp is an AI-powered agent designed to assist cryptocurrency investors by providing investment advice. It analyzes real-time trading data, assesses fundamental trading indicators and quant models, and offers BTC exit signals based on a set of strategies.

## Functions


## Tech Architecture

Thorp AI Agent is built with a modular architecture to ensure scalability and maintainability. Below are the main components of the system:

- Data Collection: Integrates with various crypto exchanges and website to fetch real-time trading data. 
- AI Engine: MoE models and RAG to make LLM more powerful and
- Strategy Engine:10 predefined strategies for BTC exit signals based on historical market patterns and technical analysis.
- Signal Generation:Signals are generated based on real-time analysis of market data, with configurable thresholds for risk levels and strategy selection.
- API Layer: Exposes endpoints for external applications to query the agent’s recommendations.
- Backend: A robust backend to manage real-time data flow, execution of trading strategies, and notifications.
- Frontend (Optional): A simple dashboard or CLI interface for users to monitor signals and adjust settings.

## Roadmap

### Data Collection:
- [x] Integrate Cryptocurrency Exchange APIs（OKX）
- [ ] Collect Social Media Data
- [ ] Collect On Chain Data
      
### AI Engine
- [x] LLM（ChatGPT-o1）
- [x] Knowledge Graph
- [ ] AI Agent
- [x] RAG
- [ ] MoE
### Strtegy Engine
- [x] Strategy Design & Integration
- [ ] Strategy Combination Optimization
- [ ] Testing & Backtesting
### API Layer
- [ ] API Design & Implementation
- [ ] Data Caching & Performance Optimization
- [ ] Security & Authentication

### Backend
- [ ] Social Media Integration (Twitter, Telegram, WeChat, etc.)
- [ ] Data Storage & Management
- [ ] Performance Optimization & Monitoring

### Frontend
- [x] Official Website
- [x] question-answering Interface
- [ ] Real-time Signal Push & Notifications
- [ ] Data Visualization


## Strategy and index
- [x] Pi Cycle
- [x] S2F
- [ ] MVRV z-score
- [ ] Mayer Multiple
- [ ] Fear & greed index
   
- [ ] RSI
- [ ] Hash Bonding
- [ ] MACD
- [ ] STH MVRV
- [ ] Bollinger Band

## Quick Start

1. Clone the repository
   ``` git clone https://github.com/yourusername/thorp-ai-agent.git ```
2. Install the required dependencies
3. Set up your API keys for real-time trading data access.
4. Run the agent.


## Join Us
We welcome contributions from the community! Feel free to fork the repository and submit pull requests.

Please follow the steps below to contribute:
- Fork this repository
- Create your feature branch
- Commit your changes
- Push to the branch
- Open a pull request

## License
This project is licensed under the MIT License.
