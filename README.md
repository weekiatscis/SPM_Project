# Smart Task Manager

A collaborative task management application designed to help teams stay organized and on track. Built with microservices architecture and Scrum methodology, it enables users to create and manage tasks, organize them into projects, track deadlines, receive real-time notifications, and generate comprehensive progress reports.

## 🚀 Features

### Core Features
- **Task Management**: Create, update, delete, and track tasks with full CRUD operations
- **Project Organization**: Group related tasks into projects for better organization
- **Recurring Tasks**: Automatically create tasks based on daily, weekly, monthly, or yearly schedules
- **Comments & Mentions**: Collaborate with team members using @mentions in task comments
- **Real-time Notifications**: Email and in-app notifications for task updates, comments, and due dates
- **Progress Reports**: Generate detailed project insights with task breakdown and completion analytics
- **Role-Based Access Control**: Manage permissions for Manager, Staff, and Director roles
- **Audit Logs**: Track all task changes with comprehensive audit trails
- **Dashboard Analytics**: Visualize project progress with charts and metrics
- **User Authentication**: Secure login with account locking and password reset functionality

### Advanced Features
- **Custom Reminder Days**: Configure personalized reminder schedules (e.g., 7, 3, 1 days before due date)
- **Subtasks**: Break down complex tasks into manageable subtasks
- **Task Filtering**: Filter by status, priority, owner, and project
- **Overdue Detection**: Automatically identify and flag overdue tasks
- **Profile Management**: Update user information and preferences
- **WebSocket Support**: Real-time updates across all connected clients

## 🏗️ Architecture

This project follows a **microservices architecture** for scalability and maintainability:

### Frontend
- **Framework**: Vue.js 3 with Composition API
- **UI Library**: Ant Design Vue
- **State Management**: Pinia
- **Routing**: Vue Router
- **Styling**: Tailwind CSS
- **Charts**: ECharts (via vue-echarts)
- **Build Tool**: Vite
- **Real-time**: Socket.IO Client

### Backend Microservices
- **Task Service** (Port 8080): Task CRUD, recurring tasks, comments, notifications
- **Notification Service** (Port 8084): Email notifications, WebSocket, real-time alerts
- **Project Service** (Port 8082): Project management and organization
- **User Service** (Port 8081): User management and profiles
- **Auth Service** (Port 8086): Authentication and authorization
- **Report Service** (Port 8090): Analytics and progress reports

### Infrastructure
- **Database**: Supabase (PostgreSQL)
- **Message Queue**: RabbitMQ (for asynchronous notifications)
- **Containerization**: Docker & Docker Compose
- **Language**: Python 3 (Flask) for backend, JavaScript (Vue.js) for frontend

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js**: v18.0.0 or higher ([Download](https://nodejs.org/))
- **Python**: 3.9 or higher ([Download](https://www.python.org/downloads/))
- **Docker**: Latest version ([Download](https://www.docker.com/get-started))
- **Docker Compose**: Usually included with Docker Desktop
- **npm**: Comes with Node.js
- **Git**: For version control ([Download](https://git-scm.com/))

### Accounts Required
- **Supabase Account**: For database ([Sign up](https://supabase.com/))
- **Email Provider**: Gmail, SendGrid, or similar for SMTP

## 🛠️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/SPM_Project.git
cd SPM_Project
```

### 2. Install Frontend Dependencies
```bash
npm install
```

### 3. Install Python Dependencies (Optional - for local development)
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory by copying the example:

```bash
cp .env.example .env
```

Then edit `.env` with your actual credentials:

```env
# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# RabbitMQ Configuration (use default for Docker)
RABBITMQ_URL=amqp://localhost

# Service URLs (use these for development)
NOTIFICATION_SERVICE_URL=http://localhost:8084
TASK_SERVICE_URL=http://localhost:8080
VITE_REPORT_SERVICE_URL=http://localhost:8090

# Email Configuration
# For Gmail: Generate App Password at https://myaccount.google.com/apppasswords
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
FROM_EMAIL=your_email@gmail.com
FROM_NAME=Smart Task Manager

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

#### Getting Supabase Credentials:
1. Create a project at [supabase.com](https://supabase.com)
2. Go to Project Settings → API
3. Copy your Project URL and service_role key (keep this secret!)

#### Setting up Gmail App Password:
1. Enable 2-Factor Authentication on your Google Account
2. Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use this 16-character password in your `.env` file

### 5. Start Backend Services with Docker

**First time setup** (builds and starts all containers):
```bash
docker-compose up --build
```

**Subsequent runs** (uses cached images):
```bash
docker-compose up
```

**Run in background** (detached mode):
```bash
docker-compose up -d
```

**Check service status:**
```bash
docker-compose ps
```

**View logs:**
```bash
docker-compose logs -f
```

**Stop all services:**
```bash
docker-compose down
```

### 6. Start Frontend Development Server

In a separate terminal:
```bash
npm run dev
```

The application will be available at **http://localhost:5173**

### 7. Access Services

Once everything is running:
- **Frontend**: http://localhost:5173
- **Task Service**: http://localhost:8080
- **User Service**: http://localhost:8081
- **Project Service**: http://localhost:8082
- **Notification Service**: http://localhost:8084
- **Auth Service**: http://localhost:8086
- **Report Service**: http://localhost:8090
- **RabbitMQ Management UI**: http://localhost:15672 (admin/admin123)



## 🔌 API Documentation

### Task Service (Port 8080)

#### Tasks
- `GET /tasks` - Get all tasks (with filters)
- `GET /tasks/:id` - Get task by ID
- `POST /tasks` - Create a new task
- `PUT /tasks/:id` - Update a task
- `DELETE /tasks/:id` - Delete a task
- `GET /tasks/:id/subtasks` - Get task subtasks
- `GET /tasks/user/:user_id` - Get tasks by user

#### Comments
- `GET /tasks/:id/comments` - Get task comments
- `POST /tasks/:id/comments` - Add a comment

#### Recurring Tasks
- `GET /tasks/:id/recurring-preview` - Preview recurring instances
- `POST /tasks/:id/stop-recurrence` - Stop task recurrence

#### Notifications
- `POST /tasks/notifications/check-all` - Check all task notifications
- `GET /tasks/:id/notification-preferences` - Get notification preferences

#### Audit Logs
- `GET /tasks/:id/logs` - Get task audit logs

### Notification Service (Port 8084)
- `GET /notifications` - Get user notifications
- `POST /notifications/realtime` - Send real-time notification
- `PUT /notifications/:id/read` - Mark notification as read
- `DELETE /notifications/:id` - Delete notification

### Project Service (Port 8082)
- `GET /projects` - Get all projects
- `GET /projects/:id` - Get project by ID
- `POST /projects` - Create a project
- `PUT /projects/:id` - Update a project
- `DELETE /projects/:id` - Delete a project

### User Service (Port 8081)
- `GET /users` - Get all users
- `GET /users/:id` - Get user by ID
- `PUT /users/:id` - Update user profile

### Auth Service (Port 8086)
- `POST /login` - User login
- `POST /logout` - User logout
- `POST /register` - User registration
- `POST /forgot-password` - Request password reset
- `POST /reset-password` - Reset password
- `GET /health` - Health check

### Report Service (Port 8090)
- `GET /reports/project/:id` - Generate project report
- `GET /health` - Health check

## 🧪 Testing

### Run Frontend Tests
```bash
npm test
```

### Run Backend Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_account_locking.py -v
```

### Test Coverage
```bash
pytest --cov=src tests/
```

## 🔧 Development

### Building for Production

**Build Frontend:**
```bash
npm run build
```

**Preview Production Build:**
```bash
npm run preview
```

### Code Quality

**Linting** (if configured):
```bash
npm run lint
```

### Database Migrations

If you need to update the database schema:
1. Update your Supabase database via the Supabase Dashboard
2. Or use SQL migrations in Supabase SQL Editor

## 🐛 Troubleshooting

### Docker Containers Won't Start

**Issue**: Ports are already in use
```bash
# Check what's using the port
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # Mac/Linux

# Stop all containers and restart
docker-compose down
docker-compose up --build
```

**Issue**: Docker daemon not running
- Start Docker Desktop application
- Wait for it to fully initialize
- Try `docker-compose up` again

### Database Connection Errors

**Issue**: `Connection refused` or `Invalid credentials`
- Verify Supabase credentials in `.env`
- Check that your Supabase project is active
- Ensure service role key (not anon key) is used
- Test connection at https://supabase.com/dashboard/project/_/settings/api

### RabbitMQ Connection Failed

**Issue**: Services can't connect to RabbitMQ
```bash
# Check RabbitMQ is running
docker ps | grep rabbitmq

# View RabbitMQ logs
docker logs rabbitmq

# Restart RabbitMQ
docker-compose restart rabbitmq
```

### Email Notifications Not Working

**Issue**: SMTP authentication failure
- For Gmail: Ensure 2FA is enabled and you're using an App Password (not regular password)
- Check SMTP credentials in `.env`
- Verify SMTP_HOST and SMTP_PORT are correct
- Test with: https://www.smtper.net/

**Issue**: Emails going to spam
- Add SPF/DKIM records (if using custom domain)
- Use reputable SMTP provider (SendGrid, AWS SES)
- Avoid spam trigger words in email content

### Frontend Not Loading

**Issue**: Blank page or build errors
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

**Issue**: API calls failing (CORS errors)
- Ensure all microservices are running
- Check service URLs in `.env`
- Verify CORS is enabled in Flask services

### Services Not Healthy in Docker

**Issue**: Container exits or health check fails
```bash
# Check specific service logs
docker-compose logs task-service

# Rebuild specific service
docker-compose up --build task-service

# Check health status
docker inspect task-service | grep Health
```

### Port Conflicts

**Issue**: "Port already in use"
```bash
# Option 1: Stop conflicting service
# Find and kill process using the port (example: 8080)
# Windows:
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8080 | xargs kill -9

# Option 2: Change ports in docker-compose.yml
# Edit docker-compose.yml and change exposed ports
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create your feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Coding Standards
- Follow existing code style
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

### Branch Naming Convention
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Urgent production fixes
- `chore/` - Maintenance tasks

## 👥 Team

**Smart Task Manager Team**
- Project built as part of Software Project Management course
- Contact: [Your email or team contact]

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Vue.js](https://vuejs.org/)
- UI components from [Ant Design Vue](https://antdv.com/)
- Database powered by [Supabase](https://supabase.com/)
- Charts powered by [Apache ECharts](https://echarts.apache.org/)
- Styled with [Tailwind CSS](https://tailwindcss.com/)

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Vue.js Documentation](https://vuejs.org/guide/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)

## 🔐 Security

- Never commit `.env` file to version control
- Keep Supabase service role key secret
- Use HTTPS in production
- Regularly update dependencies
- Enable rate limiting in production
- Use strong passwords and enable 2FA

## 📊 Performance

- Frontend built with Vite for fast HMR
- Backend services are stateless and horizontally scalable
- Database queries optimized with proper indexing
- Caching implemented for user data
- WebSocket for real-time updates to reduce polling

---

**Need help?** Open an issue on GitHub or contact the team.

**Happy Task Managing! 🚀**
