# שלב 1: שלב הבנייה (Base image)
FROM python:3.11-slim as builder
# ... (הגדרות סביבה והתקנת requirements.txt) ...

# שלב 2: שלב הסופי (Runtime image)
FROM python:3.11-slim
# ... (הגדרות סביבה) ...
WORKDIR $APP_HOME

# העתקת התלויות המותקנות
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# --- 🎯 התיקון: התקנת curl ---
# עדכון רשימת החבילות והתקנת curl (חיוני עבור start.sh)
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*
# --- סוף התיקון ---

# ... (שאר העתקות והגדרת הרשאות)
COPY . .
RUN chmod +x $APP_HOME/start.sh
EXPOSE 8080
CMD ["/bin/bash", "start.sh"]
