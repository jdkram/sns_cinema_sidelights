include(${CMAKE_CURRENT_LIST_DIR}/sequences/CMakeLists.txt)
include(${CMAKE_CURRENT_LIST_DIR}/events/CMakeLists.txt)

list(APPEND SOURCES
        "${CMAKE_CURRENT_LIST_DIR}/main.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/CDigitalButton.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/CLEDManager.cpp"
        "${CMAKE_CURRENT_LIST_DIR}/CSequenceManager.cpp"
        )