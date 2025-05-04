# Agentverse Sample Projects

A collection of sample projects demonstrating the capabilities of the Agentverse platform for building autonomous marketing agents. These projects serve as examples and starting points for developers and marketing professionals interested in leveraging AI-driven solutions for social media campaigns using the Agentverse platform.

**Important**
To acess the Idea Validator Please visit
https://github.com/bg073/fetch.ai_Hackathon2025_BusinessValidator.git - sadly it is just script, Due to time limitations, Please run "Run.py"


## Overview

This repository contains a sample project showcasing a multi-agent system for creating, posting, and analyzing marketing content on X (Twitter). The project demonstrates how to use AI to generate ad content, create engaging images, post to social media, and track performance, providing a foundation for building sophisticated marketing automation tools.

## Sample Projects

### 1. AI Marketing Agent for X (Twitter)

**Track**: Creator Economy

A multi-agent system that automates the creation and posting of marketing content on X (Twitter). It uses AI to generate ad text, create engaging images, post tweets, and track performance, helping marketers optimize their social media campaigns.

**Key Features**:
- AI-generated ad content using the Gemini API for compelling tweet text
- Dynamic image generation with Pollinations API for visually appealing posts
- Automated posting to X (Twitter) with support for multiple images
- Performance tracking to analyze tweet engagement and suggest improvements
- Interactive CLI and Streamlit web interface for user interaction
- Customizable campaign questions to tailor content to specific products

[View Project →](./x-marketing-agent)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Firefox and geckodriver (for Selenium-based image scraping)
- API keys for Gemini, Twitter (X), and Pollinations (optional for image generation)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/x-marketing-agent.git
   cd x-marketing-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables by copying the `.env.template` to `.env` and filling in your API keys:
   ```bash
   cp .env.template .env
   ```
   Required keys:
   - `GEMINI_API_KEY`: For ad content generation
   - `TWITTER_API_KEY`, `TWITTER_API_KEY_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_TOKEN_SECRET`, `TWITTER_USER_ACCESS_TOKEN`: For Twitter API access
   - `TWITTER_BEARER_TOKEN`: For Twitter API v2 searches
   - `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, `TWITTER_REDIRECT_URI`: For OAuth 2.0 flow (optional)

4. Run the CLI or web interface:
   - CLI: `python cli_marketing_agent.py`
   - Web UI: `streamlit run webui_streamlit.py`

## Project Structure

The project follows a modular structure:

```
x-marketing-agent/
├── README.md                 # Project documentation
├── .env.template             # Template for environment variables
├── requirements.txt          # Dependencies
├── ad_strategy.py            # Tracks ad performance metrics
├── cli_marketing_agent.py    # CLI interface for interacting with the agent
├── gemini_utils.py           # Utilities for Gemini API integration
├── selenium_utils.py         # Image scraping utilities using Selenium
├── trend_agent.py            # Main agent for generating and posting ad content
├── twitter_utils.py          # Twitter API interaction utilities
├── webui_streamlit.py        # Streamlit web interface for user interaction
└── uploads/                  # Directory for storing generated images
```

## Extending the Project

This sample project is designed to be a starting point. Here are some ways you can extend it:

1. **Add Support for More Platforms**: Integrate with other social media platforms like Instagram or LinkedIn.
2. **Enhance Image Generation**: Incorporate advanced image generation models or allow for custom image styles.
3. **Improve Performance Analysis**: Add more sophisticated metrics and A/B testing capabilities.
4. **Automate Scheduling**: Implement a scheduling system to post content at optimal times.
5. **Multilingual Support**: Integrate with translation APIs to create content in multiple languages.

## Acknowledgments

- [Fetch.ai](https://fetch.ai/) for the uAgents framework
- Google for the Gemini API
- Twitter (X) for their API and developer tools
- Pollinations for their AI image generation API
- All contributors who have helped improve this sample project
