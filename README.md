# Fiindo Recruitment Challenge

This repository contains a coding challenge for fiindo candidates. Candidates should fork this repository and implement their solution based on the requirements below.

## Challenge Overview

Create a data processing application that:
- Fetches financial data from an API
- Performs calculations on stock ticker data
- Saves results to a SQLite database
- Demonstrates proficiency in API integration, data manipulation, and database operations

## Skills Tested

- **API Integration**: Working with REST APIs and handling responses
- **Data Processing**: Cleaning, transforming, and aggregating data
- **ORM/Database**: SQLite database design and operations
- **Debugging**: Troubleshooting API calls and data processing logic
- **Code Quality**: Clean, maintainable, and well-documented code

## Technical Requirements

### Input
- **API Endpoint**: `https://api.test.fiindo.com` (docs: `https://api.test.fiindo.com/api/v1/docs/`)
- **Authentication**: Use header `Auhtorization: Bearer {first_name}.{last_name}` with every request.
- **Template**: This forked repository as starting point

### Output
- **Database**: SQLite database with processed financial data
- **Tables**: Individual ticker statistics and industry aggregations

## Process Steps

### 1. Data Collection
- Connect to the Fiindo API
- Authenticate using your identifier
- Fetch financial data for multiple stock tickers

### 2. Data Calculations

#### Per Ticker Statistics
- **PE Ratio**: Price-to-Earnings ratio calculation
- **Revenue Growth**: Quarter-over-quarter revenue growth (Q-1 vs Q-2)

#### Industry Aggregation
- **Average PE Ratio**: Mean PE ratio across all tickers in each industry
- **Average Revenue Growth**: Mean revenue growth across all tickers in each industry

### 3. Data Storage
- Design appropriate database schema
- Save individual ticker statistics
- Save aggregated industry data
- Ensure data integrity and relationships

## Database Setup

### Database Files
- `fiindo_challenge.db`: SQLite database file
- `models.py`: SQLAlchemy model definitions (can be divided into separate files if needed)
- `alembic/`: Database migration management

## Getting Started

1. **Fork this repository** to your GitHub account
2. **Review the database structure** - examine the pre-configured SQLite database and table schemas
3. **Implement the solution** following the process steps outlined above 

## Deliverables

Your completed solution should include:
- Working application that fetches data from the API
- SQLite database with calculated results
- Clean, documented code
- README with setup and run instructions

## Evaluation Criteria

- **Functionality**: Application works correctly and produces expected results
- **Code Quality**: Clean, readable, and well-organized code
- **Data Accuracy**: Calculations are mathematically correct
- **Error Handling**: Proper handling of API errors and edge cases
- **Database Design**: Appropriate schema and data relationships
- **Documentation**: Clear setup and usage instructions

## API Documentation

`https://api.test.fiindo.com/api/v1/docs/`

## Notes

- Ensure your solution is production-ready
- Handle API rate limits and potential timeouts
- Validate data before processing
- Include error logging and debugging capabilities
- Test with various data scenarios

Good luck with your implementation!
