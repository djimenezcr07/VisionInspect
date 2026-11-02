#include "inspection.hpp"
#include <opencv2/imgproc.hpp>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <stdexcept>
int main(){
 cv::Mat image(400,400,CV_8UC3,cv::Scalar(30,30,30));cv::circle(image,{200,200},130,cv::Scalar(190,190,190),-1);
 auto ok=vision::inspect(image,{});assert(ok.found);assert(ok.regions.empty());assert(std::abs(ok.cx-200)<3);assert(ok.annotated.size()==image.size());
 cv::circle(image,{180,190},10,cv::Scalar(15,15,15),-1);auto defect=vision::inspect(image,{});assert(defect.found && defect.regions.size()==1);
 cv::Mat blank(400,400,CV_8UC3,cv::Scalar(30,30,30));assert(!vision::inspect(blank,{}).found);
 bool invalid=false;try{vision::inspect(cv::Mat(),{});}catch(const std::invalid_argument&){invalid=true;}assert(invalid);
 invalid=false;try{vision::inspect(image,{90,75,0,40});}catch(const std::invalid_argument&){invalid=true;}assert(invalid);return 0;
}
