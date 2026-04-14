# groupproject_teamAG
cloud computing project

This project deploys an intelligent Telegram chatbot on the AWS EC2 cloud platform using Docker to ensure 24/7 stable operation. The bot integrates the Azure OpenAI (HKBU) API to achieve intelligent conversational responses, connects to the MongoDB Atlas cloud database to automatically store and persist chat logs in real time, and implements core functions such as context management and rate limiting through Python programs. The overall logic is: users send messages to the Telegram bot → the service on EC2 processes requests and calls the LLM API → returns AI replies → synchronizes the chat record to MongoDB, thus completing the entire cloud-based deployment and intelligent interaction process.
