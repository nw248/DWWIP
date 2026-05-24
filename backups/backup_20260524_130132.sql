-- Таблица: assignments

-- Таблица: courses
INSERT INTO courses VALUES (10,Английский язык,просто описание 
просто вторая строчка описания ,2026-05-17 12:02:22.081923);

-- Таблица: group_course

-- Таблица: group_lessons

-- Таблица: groups
INSERT INTO groups VALUES (14,ИС-22);
INSERT INTO groups VALUES (15,МС-26);

-- Таблица: lessons

-- Таблица: questions

-- Таблица: teacher_course
INSERT INTO teacher_course VALUES (33,10);

-- Таблица: test_answers

-- Таблица: users
INSERT INTO users VALUES (31,admin@example.com,pbkdf2:sha256:260000$PiEvsWOLNet42eF2$b1d5d6ac15b55a3cf1a09522a2d3d90eaba2faa5830c995ec27531c3fbf73267,Администратор,admin,NULL);
INSERT INTO users VALUES (32,student@example.com,pbkdf2:sha256:260000$sdYojMWoIJbSb4Cs$89e8e6d91d701a47b6f266ce7fb676b145fecdea27c94b5ae13d3b360ba0cba0,Кира,student,14);
INSERT INTO users VALUES (33,teacher@example.com,pbkdf2:sha256:260000$zn6i6pRhGeHMGNSm$9038fe23cc7d27c3b508d4c56dbcbf8e520f4c390fdd98bc61f029a1a6046d3d,Михаил Иванович,teacher,NULL);
INSERT INTO users VALUES (34,admin1@example.com,pbkdf2:sha256:260000$jTszH5Lxm6AvFMeK$00a35c244fe004f263afe5dff130bc1a94306384cbb8edc6ff2c4962a20d9043,АМ,admin,NULL);
INSERT INTO users VALUES (35,student1@example.com,pbkdf2:sha256:260000$4ajhyKkflhDfri2V$e086761d9ba4696b04bfa1d8884de24a6b762513e13188e7980fb7a5cc58c477,Kira,student,14);
INSERT INTO users VALUES (36,admin@test.com,pbkdf2:sha256:260000$JHqDtDMvn8iVul1v$58ff315a01c850dc7f1c8a857b58e2dd61686e43d46de12e75713269008235bd,Тест Админ,admin,NULL);

