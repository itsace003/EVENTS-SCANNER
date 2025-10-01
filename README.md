# AI Event Scanner v2.0

An intelligent AI event discovery application that uses Perplexity AI to search and curate AI-related events from Luma.com and Meetup.com. Built with FastAPI backend and React TypeScript frontend.

## 🚀 Features

### Core Functionality
- **AI-Powered Event Discovery**: Uses Perplexity AI to intelligently search for AI-related events
- **Multi-Platform Support**: Supports Luma.com and Meetup.com event sources
- **Smart Event Classification**: AI-powered relevance scoring and categorization
- **Monthly Focus**: Discover events for specific months (1-month timeframe)
- **Session-Based Tracking**: Cookie-based user sessions with watch status persistence

### User Experience
- **Clean, Modern UI**: Dark theme with responsive design
- **Event Watch Status**: Mark events as watched/unwatched
- **Advanced Filtering**: Filter by category, watch status, and relevance score
- **Real-time Updates**: Live status updates during event discovery
- **Offline-Ready**: Caches data for improved performance

### Technical Features
- **Async Architecture**: Non-blocking event discovery and API operations
- **Database Persistence**: SQLite for development, PostgreSQL-ready for production
- **Session Management**: Secure cookie-based sessions
- **Error Handling**: Comprehensive error handling and user feedback
- **Type Safety**: Full TypeScript implementation

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── models.py              # SQLAlchemy models
│   ├── database.py            # Database configuration
│   ├── perplexity_client.py   # Perplexity API client
│   ├── event_discovery.py     # Event discovery engine
│   ├── session_manager.py     # Session management
│   └── api/
│       ├── events.py          # Event endpoints
│       └── users.py           # User/session endpoints
├── requirements.txt
├── Dockerfile
└── .env.example
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/
│   │   ├── EventCard.tsx      # Event display card
│   │   └── EventDiscovery.tsx # Event discovery form
│   ├── hooks/
│   │   └── useEvents.ts       # Event management hook
│   ├── utils/
│   │   └── api.ts            # API client
│   ├── types.ts              # TypeScript definitions
│   ├── App.tsx               # Main application
│   └── main.tsx              # React entry point
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Perplexity API key

### Backend Setup

1. **Clone and navigate to backend**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment configuration**
```bash
cp .env.example .env
# Edit .env with your Perplexity API key
```

5. **Initialize database**
```bash
python -c "from app.database import create_tables; create_tables()"
```

6. **Start development server**
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## 📡 API Reference

### Event Endpoints

#### `POST /api/events/discover-events`
Discover AI events using Perplexity AI

**Request Body:**
```json
{
  "location": "San Francisco",
  "platform": "luma",
  "month": 11,
  "year": 2025
}
```

#### `GET /api/events/{month}/{year}`
Get events for a specific month

**Query Parameters:**
- `location` (optional): Filter by location
- `category` (optional): Filter by category
- `min_relevance_score` (optional): Minimum AI relevance score

#### `POST /api/events/watch`
Toggle event watch status

**Request Body:**
```json
{
  "event_id": "event-uuid",
  "watch_status": true
}
```

### User Endpoints

#### `GET /api/users/preferences`
Get user preferences

#### `PUT /api/users/preferences`
Update user preferences

#### `GET /api/users/session/stats`
Get session statistics

## 🎯 Usage Guide

### 1. Event Discovery
1. Enter your location (e.g., "San Francisco", "New York", "Online")
2. Select platform (Luma or Meetup)
3. Choose target month and year
4. Click "Discover Events" 

The AI will search for relevant events and classify them by:
- **AI Relevance Score** (1-10 scale)
- **Category** (Conference, Workshop, Networking, Talk, Hackathon)
- **Event Type** (Online, In-person, Hybrid)

### 2. Event Management
- **View Events**: Events are displayed in card format with all key information
- **Watch Status**: Click the eye icon to mark events as watched/unwatched
- **Filtering**: Use category and watch status filters to narrow results
- **External Links**: Click on event cards to open the original event page

### 3. Session Persistence
- Your preferences and watch status are automatically saved
- Sessions persist for 30 days
- No account creation required

## 🔧 Configuration

### Environment Variables

**Backend (.env)**
```bash
# Required
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Database
DATABASE_URL=sqlite:///./ai_events.db
ASYNC_DATABASE_URL=sqlite+aiosqlite:///./ai_events.db

# Optional
REDIS_URL=redis://localhost:6379
SESSION_LIFETIME_DAYS=30
COOKIE_SECURE=false
```

**Frontend**
```bash
# Optional - defaults to localhost:8000
VITE_API_BASE_URL=http://localhost:8000
```

### Platform Selection

**Luma.com (Recommended)**
- Better structured data
- More AI-focused events
- Easier to parse and classify
- JSON-LD support

**Meetup.com**
- Larger event database
- More diverse event types
- ICS feed support
- Requires more complex parsing

## 🐳 Docker Deployment

### Development
```bash
# Backend
cd backend
docker build -t ai-event-scanner-backend .
docker run -p 8000:8000 ai-event-scanner-backend

# Frontend
cd frontend
npm run build
# Serve dist/ directory with any static file server
```

### Production
```bash
# Use docker-compose for full stack deployment
docker-compose up -d
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
npm run type-check
```

## 🔍 Monitoring & Debugging

### Health Checks
- Backend: `GET /health`
- Database connectivity and API status

### Logging
- Structured JSON logging with `structlog`
- Request/response logging
- Error tracking and debugging

### Session Management
- View session stats: `GET /api/users/session/stats`
- Manual session cleanup for expired sessions

## 🛡️ Security Considerations

### Production Checklist
- [ ] Set `COOKIE_SECURE=true` for HTTPS
- [ ] Use PostgreSQL instead of SQLite
- [ ] Implement rate limiting
- [ ] Add API key rotation
- [ ] Configure CORS properly
- [ ] Set up monitoring and alerts

### Data Privacy
- No personal data collection
- Session-based tracking only
- Automatic session cleanup
- No external data sharing

## 🚀 Performance Optimization

### Backend
- Async/await for all I/O operations
- Database query optimization
- Perplexity API rate limiting
- Event deduplication and caching

### Frontend
- Lazy loading and code splitting
- Optimized React rendering
- API response caching
- Image optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Backend: Black, isort, type hints
- Frontend: ESLint, Prettier, TypeScript strict mode

## 📈 Roadmap

### Near Term
- [ ] Multiple platform support in single search
- [ ] Advanced event filtering (price, size, etc.)
- [ ] Event recommendations based on watch history
- [ ] Export functionality (calendar, CSV)

### Long Term
- [ ] Mobile app
- [ ] Real-time event updates
- [ ] Community features (comments, ratings)
- [ ] Integration with calendar systems
- [ ] AI-powered event recommendations

## 🐛 Troubleshooting

### Common Issues

**Perplexity API Errors**
- Verify API key is correct and active
- Check rate limiting (1 request per second recommended)
- Ensure proper error handling for model availability

**Database Connection Issues**
- Verify database file permissions
- Check SQLite version compatibility
- Initialize database tables properly

**Session Management**
- Clear browser cookies if session issues occur
- Check cookie settings for HTTPS deployment
- Verify session lifetime configuration

**Event Discovery Timeout**
- Increase request timeout settings
- Implement retry logic for failed requests
- Check Perplexity API status

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Perplexity AI](https://perplexity.ai) for intelligent search capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the robust backend framework
- [React](https://react.dev/) and [Vite](https://vitejs.dev/) for the modern frontend
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Lucide React](https://lucide.dev/) for icons

---

**Built with ❤️ for the AI community**