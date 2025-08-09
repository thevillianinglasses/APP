#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

user_problem_statement: |
  Implement comprehensive admin features for healthcare app including:
  1. Admin login (existing: admin@unicarepolyclinic.com / admin-007)
  2. Advanced doctor scheduling with automation (daily/weekly/holidays/leave management)
  3. Daily admin reminders for bookings
  4. Inventory management for laboratory and pharmacy
  5. Live inventory option with future EHR integration capability
  6. Campaign management system (festive offers like 10% off)
  7. Notification system (in-app + SMS 1hr before appointments)
  8. Patient feedback system after consultation completion
  9. Ensure admin can access all features

backend:
  - task: "Advanced Doctor Scheduling System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented DoctorScheduleTemplate, DoctorLeave, Holiday models and full API endpoints for schedule automation"

  - task: "Inventory Management System"
    implemented: true  
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented InventoryItem, StockTransaction models with full CRUD APIs and low stock alerts"

  - task: "Campaign Management System"
    implemented: true
    working: true 
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented Campaign model with discount/festive offer management and active campaign APIs"

  - task: "Notification System with SMS"
    implemented: true
    working: true
    file: "server.py" 
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented Notification model, SMS integration with Twilio, background scheduler for appointment reminders"

  - task: "Patient Feedback System"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0 
    priority: "medium"
    needs_retesting: true
    status_history:
      - working: true
        agent: "main"
        comment: "Implemented Feedback model with ratings, categories, and admin statistics APIs"

frontend:
  - task: "Advanced Doctor Scheduling Interface"
    implemented: false
    working: "NA"
    file: "AdminDashboard.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Admin interface for doctor scheduling automation"

  - task: "Inventory Management Interface"
    implemented: false
    working: "NA"
    file: "AdminDashboard.js"
    stuck_count: 0
    priority: "high" 
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Admin interface for pharmacy and lab inventory"

  - task: "Campaign Management Interface"
    implemented: false
    working: "NA"
    file: "AdminDashboard.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main" 
        comment: "Admin interface for creating and managing campaigns"

  - task: "Notification Management Interface"
    implemented: false
    working: "NA"
    file: "AdminDashboard.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:  
      - working: "NA"
        agent: "main"
        comment: "In-app notification display and management"

  - task: "Patient Feedback Interface"
    implemented: false
    working: "NA"
    file: "components/"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
      - working: "NA"
        agent: "main"
        comment: "Patient feedback collection and admin review interface"

metadata:
  created_by: "main_agent"
  version: "1.0" 
  test_sequence: 0
  run_ui: false

test_plan:
  current_focus:
    - "Advanced Doctor Scheduling System"
    - "Inventory Management System"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
  - agent: "main"
    message: "Starting comprehensive admin features implementation. Beginning with advanced doctor scheduling system, then inventory management, campaigns, notifications, and feedback systems."