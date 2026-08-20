#include <ros/ros.h>
#include <mavros_msgs/State.h>
#include <mavros_msgs/SetMode.h>
#include <mavros_msgs/CommandBool.h>
#include <mavros_msgs/PositionTarget.h>
#include <nav_msgs/Odometry.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/TwistStamped.h>

typedef enum FlightState
{
    INIT_PARAM = 1,
    TAKEOFF,
    HOVER,
    RUNNING,
    LANDING
};

class FlightManage{
    public:
        FlightManage();
        void initFlight();
        void takeOff();
        void run();
        void land();
    private:
        float take_off_height_;
        FlightState flight_state_;
        ros::Publisher mavros_raw_setpoint_publisher_;
        ros::Subscriber current_pose_subscriber_;

};