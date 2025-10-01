-- Схема базы данных для платформы "Конфорка"
-- PostgreSQL с поддержкой JSON для гибких схем

-- Таблица пользователей
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    bio TEXT,
    
    -- Профессиональные данные
    education JSONB, -- массив объектов {degree, institution, year}
    skills TEXT[], -- массив навыков
    experience_years INTEGER,
    
    -- Роль в системе
    user_type VARCHAR(50) CHECK (user_type IN ('researcher', 'mentor', 'equipment_provider', 'enterprise', 'student')),
    
    -- Рейтинги и статистика
    rating DECIMAL(3,2) DEFAULT 0.0,
    completed_projects INTEGER DEFAULT 0,
    
    -- Контакты и соцсети
    social_links JSONB, -- {linkedin, github, website}
    
    -- Статус и настройки
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    notification_settings JSONB DEFAULT '{}',
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Таблица проектов
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    short_description VARCHAR(1000),
    
    -- Категория и направление
    category VARCHAR(100), -- биология, физика, IT, etc.
    tags TEXT[],
    
    -- Стадия проекта
    stage VARCHAR(50) CHECK (stage IN ('idea', 'prototype', 'testing', 'commercialization', 'completed')),
    
    -- Требования к команде
    required_skills TEXT[],
    max_team_size INTEGER,
    
    -- Оборудование и ресурсы
    required_equipment JSONB, -- [{equipment_id, quantity, priority}]
    budget_estimate DECIMAL(12,2),
    -- Детализированные 16 полей концепции (гибко в JSONB)
    details JSONB,
    
    -- Автор проекта
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Статус проекта
    status VARCHAR(50) CHECK (status IN ('active', 'paused', 'completed', 'cancelled')) DEFAULT 'active',
    
    -- Визуальные материалы
    images JSONB, -- массив URL изображений
    documents JSONB, -- массив документов
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Таблица команд и участников
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Роль в команде
    role VARCHAR(100), -- лидер, разработчик, исследователь, менеджер
    responsibilities TEXT,
    
    -- Статус участия
    status VARCHAR(50) CHECK (status IN ('pending', 'active', 'completed', 'left')),
    
    -- Вклад в проект
    contribution_score INTEGER DEFAULT 0,
    
    -- Даты участия
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP,
    
    UNIQUE(project_id, user_id)
);

-- Таблица оборудования
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    manufacturer VARCHAR(200),
    model VARCHAR(200),
    
    -- Владелец оборудования
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    owner_type VARCHAR(50), -- university, enterprise, private
    
    -- Местоположение
    location JSONB, -- {address, city, coordinates}
    
    -- Технические характеристики
    specifications JSONB,
    images JSONB,
    
    -- Условия аренды
    rental_price_per_hour DECIMAL(10,2),
    rental_price_per_day DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    
    -- Доступность
    availability_calendar JSONB, -- сложный график доступности
    booking_lead_time_hours INTEGER DEFAULT 24,
    
    -- Требования к пользователю
    required_certifications TEXT[],
    required_training BOOLEAN DEFAULT false,
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    is_available BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица бронирования оборудования
CREATE TABLE equipment_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Время бронирования
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    
    -- Статус бронирования
    status VARCHAR(50) CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')),
    
    -- Финансовые детали
    total_cost DECIMAL(10,2),
    payment_status VARCHAR(50) CHECK (payment_status IN ('pending', 'paid', 'refunded')),
    
    -- Цели использования
    purpose TEXT,
    special_requirements TEXT,
    
    -- Отзывы и оценки
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_review TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица менторов
CREATE TABLE mentors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Экспертиза
    expertise_areas TEXT[],
    industry_experience INTEGER,
    companies_founded INTEGER DEFAULT 0,
    
    -- Достижения
    achievements TEXT,
    education_details TEXT,
    
    -- Условия консультаций
    consultation_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    consultation_duration_minutes INTEGER DEFAULT 60,
    
    -- Расписание
    availability_schedule JSONB, -- {days: [], hours: {start, end}}
    
    -- Статистика
    total_consultations INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0.0,
    
    -- Контент
    articles JSONB, -- опубликованные статьи и советы
    
    -- Статус
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица консультаций
CREATE TABLE consultations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mentor_id UUID REFERENCES mentors(id) ON DELETE CASCADE,
    client_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id),
    
    -- Детали консультации
    scheduled_time TIMESTAMP NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    format VARCHAR(50) CHECK (format IN ('online', 'offline', 'phone')),
    
    -- Тематика
    topics TEXT[],
    client_questions TEXT,
    
    -- Финансовые детали
    price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'RUB',
    payment_status VARCHAR(50) CHECK (payment_status IN ('pending', 'paid', 'refunded')),
    
    -- Статус консультации
    status VARCHAR(50) CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled')),
    
    -- Отзывы и оценки
    client_rating INTEGER CHECK (client_rating >= 1 AND client_rating <= 5),
    client_review TEXT,
    mentor_notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица R&D-заказов
CREATE TABLE rd_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enterprise_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Описание заказа
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    technical_requirements TEXT,
    expected_outcomes TEXT,
    
    -- Категория и теги
    category VARCHAR(100),
    tags TEXT[],
    
    -- Призовой фонд
    prize_fund DECIMAL(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    number_of_winners INTEGER DEFAULT 1,
    
    -- Критерии оценивания
    evaluation_criteria JSONB, -- [{criterion, weight, description}]
    
    -- Сроки
    submission_deadline TIMESTAMP NOT NULL,
    announcement_date TIMESTAMP,
    
    -- Статус
    status VARCHAR(50) CHECK (status IN ('open', 'reviewing', 'completed', 'cancelled')),
    
    -- Визуальные материалы
    attachments JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица участия в R&D-заказах
CREATE TABLE rd_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rd_order_id UUID REFERENCES rd_orders(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    team_lead_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Решение
    solution_description TEXT,
    solution_files JSONB,
    
    -- Статус
    status VARCHAR(50) CHECK (status IN ('submitted', 'under_review', 'winner', 'not_selected')),
    
    -- Оценка
    score DECIMAL(5,2),
    evaluation_feedback TEXT,
    
    -- Награда
    prize_amount DECIMAL(12,2),
    
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP
);

-- Таблица отзывов и рейтингов
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reviewer_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Тип отзыва
    review_type VARCHAR(50) CHECK (review_type IN ('team_member', 'mentor', 'equipment_user', 'project_partner')),
    
    -- Содержание отзыва
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    
    -- Контекст
    project_id UUID REFERENCES projects(id),
    consultation_id UUID REFERENCES consultations(id),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица уведомлений
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Тип и содержание
    type VARCHAR(50) CHECK (type IN ('project_invite', 'booking_confirmation', 'consultation_reminder', 'rd_order_update')),
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    
    -- Данные для действий
    action_data JSONB, -- {project_id, booking_id, etc.}
    
    -- Статус
    is_read BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для производительности
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_type ON users(user_type);
CREATE INDEX idx_users_rating ON users(rating DESC);

CREATE INDEX idx_projects_author_id ON projects(author_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_category ON projects(category);
CREATE INDEX idx_projects_created_at ON projects(created_at DESC);
-- Индекс для полнотекстового/фильтрационного доступа к details
CREATE INDEX IF NOT EXISTS idx_projects_details ON projects USING GIN(details);

CREATE INDEX idx_team_members_project_id ON team_members(project_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_team_members_status ON team_members(status);

CREATE INDEX idx_equipment_owner_id ON equipment(owner_id);
CREATE INDEX idx_equipment_category ON equipment(category);
CREATE INDEX idx_equipment_is_available ON equipment(is_available);

CREATE INDEX idx_equipment_bookings_equipment_id ON equipment_bookings(equipment_id);
CREATE INDEX idx_equipment_bookings_project_id ON equipment_bookings(project_id);
CREATE INDEX idx_equipment_bookings_start_time ON equipment_bookings(start_time);

CREATE INDEX idx_mentors_user_id ON mentors(user_id);
CREATE INDEX idx_mentors_expertise_areas ON mentors USING GIN(expertise_areas);
CREATE INDEX idx_mentors_is_active ON mentors(is_active);

CREATE INDEX idx_consultations_mentor_id ON consultations(mentor_id);
CREATE INDEX idx_consultations_client_id ON consultations(client_id);
CREATE INDEX idx_consultations_scheduled_time ON consultations(scheduled_time);

CREATE INDEX idx_rd_orders_enterprise_id ON rd_orders(enterprise_id);
CREATE INDEX idx_rd_orders_status ON rd_orders(status);
CREATE INDEX idx_rd_orders_submission_deadline ON rd_orders(submission_deadline);

CREATE INDEX idx_rd_submissions_rd_order_id ON rd_submissions(rd_order_id);
CREATE INDEX idx_rd_submissions_project_id ON rd_submissions(project_id);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);

-- Триггеры для обновления временных меток
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_equipment_updated_at BEFORE UPDATE ON equipment 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mentors_updated_at BEFORE UPDATE ON mentors 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();