#pragma once
#include <opencv2/core.hpp>
#include <string>
#include <vector>
namespace vision {
struct Parameters { int foreground=90; int darkness=75; int min_area=35; int min_radius=40; };
struct Region { int x,y,width,height; double area; };
struct Result { bool found=false; int cx=0,cy=0,radius=0; std::vector<Region> regions; std::string warning; cv::Mat annotated; };
Result inspect(const cv::Mat& image, const Parameters& params);
}
