-- Таблица: assignments
INSERT INTO assignments VALUES (2,2,5,NULL,NULL,2,Результат: 2 из 2 правильных ответов,2026-05-25 16:54:14.598806);

-- Таблица: courses
INSERT INTO courses VALUES (1,1Тестовый курс,Тестовое описание,2026-05-25 15:31:39.091302);

-- Таблица: group_course
INSERT INTO group_course VALUES (1,1);

-- Таблица: group_lessons
INSERT INTO group_lessons VALUES (2,1,2,2026-05-25 16:12:12.283925);
INSERT INTO group_lessons VALUES (3,1,3,2026-05-25 16:12:17.209291);
INSERT INTO group_lessons VALUES (5,1,5,2026-05-25 16:51:45.389974);

-- Таблица: groups
INSERT INTO groups VALUES (1,ИС-22);

-- Таблица: lessons
INSERT INTO lessons VALUES (2,ф,фффф,text,NULL,1,2026-05-25 16:12:12.281794);
INSERT INTO lessons VALUES (3,ф,ффффффф,lecture,NULL,1,2026-05-25 16:12:17.208449);
INSERT INTO lessons VALUES (5,фыв,фыв,test,NULL,1,2026-05-25 16:51:45.387581);

-- Таблица: questions
INSERT INTO questions VALUES (3,ф,['фы', 'фыв'],['B', 'A'],5);
INSERT INTO questions VALUES (4,фыфывфыв,['фыввф', 'вывыфв', 'фывфывфывфыв', 'йцуйцу', 'кря'],['E'],5);

-- Таблица: teacher_course
INSERT INTO teacher_course VALUES (3,1);

-- Таблица: test_answers
INSERT INTO test_answers VALUES (1,2,3,A,True);
INSERT INTO test_answers VALUES (2,2,4,E,True);

-- Таблица: users
INSERT INTO users VALUES (1,admin@example.com,pbkdf2:sha256:260000$gNVGvOPmNaz8Si0i$7aa039f94aba375fc2d058a2cb47ec6b7c416e10d76a4cab67e56a7186a5c560,Администратор,admin,NULL);
INSERT INTO users VALUES (3,teacher@example.com,pbkdf2:sha256:260000$onBujh8yWrg1Qw3h$0538502f3993cdcb575e8e2dc1f5afe659ea0989328a1fe8a8dd4c960389cbba,Михаил Иванович,teacher,NULL);
INSERT INTO users VALUES (2,student@example.com,pbkdf2:sha256:260000$3YevxQKHECLL9uMk$f1d03efc87bbb1c44a2166b656ad18a7e1731fefdcb28a70f8396c73876a5e8b,Кира,student,1);

