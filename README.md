# ResumeMate

ResumeMate is an AI-powered resume agent platform that combines static resume presentation with interactive AI Q&A features.

🚀 **Live Demo**: [https://huggingface.co/spaces/sacahan/resumemate-chat](https://huggingface.co/spaces/sacahan/resumemate-chat)

## Core Features

- **Smart Q&A:** Personalized resume conversations powered by RAG technology
- **Contact Information Queries:** Dedicated tool for quick contact information responses
- **Conversational Contact Collection:** Collect contact information via natural language, suitable for iframe embedding
- **Bilingual Support:** Seamless switching between English and Chinese interfaces
- **Responsive Design:** Optimized experience across all screen sizes
- **JSON-Driven Content:** Flexible data management with version control

## Tech Stack

- **Frontend:** HTML + Tailwind CSS, responsive design
- **Backend:** Python + Gradio + OpenAI SDK
- **Database:** ChromaDB vector database
- **Deployment:** GitHub Pages + HuggingFace Spaces
  - **AI Chat Interface**: [HuggingFace Space](https://huggingface.co/spaces/sacahan/resumemate-chat)
  - **Static Resume**: GitHub Pages

## Quick Start

Please refer to the [Development Setup Guide](DEVELOPMENT.md) to set up your development environment.

### Prerequisites

- Python 3.10 or above
- Git
- OpenAI API key

### Setup Steps

1. Clone the repository

   ```bash
   git clone https://github.com/sacahan/ResumeMate.git
   cd ResumeMate
   ```

2. Run the environment setup script

   ```bash
   chmod +x scripts/setup_dev_env.sh
   ./scripts/setup_dev_env.sh
   ```

3. Edit the `.env` file and add your OpenAI API key

## Project Structure

See the [Development Setup Guide](DEVELOPMENT.md) for details about the project structure.

## Development Plan

For detailed development plans, see the [Development Plan Document](plans/development_plan.md).

## Project Status

### 🎉 Phase 2 Complete (Analysis Agent MVP + Frontend Foundation)

#### ✅ Backend Core Features

- **Analysis Agent**: Complete dual-tool strategy implementation
  - `get_contact_info`: Dedicated contact information query tool
  - `rag_search_tool`: Resume content retrieval tool
- **Evaluate Agent**: Multi-state evaluation system with quality control
- **Async Architecture**: High-performance async/await processing pattern

#### ✅ Frontend Complete Features

- **Responsive Resume Site**: Complete HTML5 + Tailwind CSS implementation
- **Bilingual Support**: Seamless Chinese/English switching mechanism
- **JSON Data Management**: Dynamic loading with version control system
- **Interactive Effects**: Smooth scrolling, animations, chat examples

#### ✅ Testing & Quality Assurance

- **Unit Tests**: Complete Analysis Agent test coverage
- **Integration Tests**: Frontend-backend cooperation validation
- **Contact Information Tools**: Dedicated contact information collection system

### 📋 Next Phase: Feature Enhancement & Optimization

Ready to enter Phase 3, focusing on:

- AI capability improvements and prompt optimization
- System performance optimization
- UI/UX experience enhancements
- Production deployment preparation

## Contribution Guide

1. Fork the project
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
