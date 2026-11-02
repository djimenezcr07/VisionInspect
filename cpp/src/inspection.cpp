#include "inspection.hpp"
#include <opencv2/imgproc.hpp>
#if CV_VERSION_MAJOR >= 5
#include <opencv2/geometry/2d.hpp>
#endif
#include <algorithm>
#include <cmath>
#include <stdexcept>
namespace vision {
Result inspect(const cv::Mat& image,const Parameters& p) {
 if(image.empty()||image.type()!=CV_8UC3||image.cols<64||image.rows<64||image.cols>4096||image.rows>4096) throw std::invalid_argument("Se requiere imagen BGR de 8 bits, entre 64 y 4096 píxeles por lado.");
 if(p.foreground<30||p.foreground>220||p.darkness<0||p.darkness>200||p.min_area<1||p.min_area>100000||p.min_radius<10||p.min_radius>2000) throw std::invalid_argument("Parámetros fuera del rango permitido.");
 Result out; out.annotated=image.clone(); cv::Mat gray,blurred,binary;
 cv::cvtColor(image,gray,cv::COLOR_BGR2GRAY); cv::GaussianBlur(gray,blurred,cv::Size(5,5),0);
 cv::threshold(blurred,binary,p.foreground,255,cv::THRESH_BINARY);
 cv::morphologyEx(binary,binary,cv::MORPH_CLOSE,cv::getStructuringElement(cv::MORPH_ELLIPSE,cv::Size(7,7)));
 std::vector<std::vector<cv::Point>> contours; cv::findContours(binary,contours,cv::RETR_EXTERNAL,cv::CHAIN_APPROX_SIMPLE);
 if(contours.empty()){out.warning="No se encontró una pieza circular con estos parámetros."; return out;}
 auto largest=std::max_element(contours.begin(),contours.end(),[](auto &a,auto &b){return cv::contourArea(a)<cv::contourArea(b);});
 double area=cv::contourArea(*largest),perimeter=cv::arcLength(*largest,true); cv::Point2f center; float radius; cv::minEnclosingCircle(*largest,center,radius);
 double circularity=perimeter>0?4*CV_PI*area/(perimeter*perimeter):0;
 if(radius<p.min_radius||circularity<0.72||area/(CV_PI*radius*radius)<0.82||radius>std::min(image.cols,image.rows)*0.49){out.warning="No se encontró una pieza circular válida; revisá el contraste y el encuadre.";return out;}
 out.found=true;out.cx=cvRound(center.x);out.cy=cvRound(center.y);out.radius=cvRound(radius);
 cv::Mat roi=cv::Mat::zeros(gray.size(),CV_8U),spots;
 cv::circle(roi,center,cvRound(radius*0.82),cv::Scalar(255),-1);
 cv::threshold(blurred,spots,p.darkness,255,cv::THRESH_BINARY_INV);cv::bitwise_and(spots,roi,spots);
 cv::morphologyEx(spots,spots,cv::MORPH_OPEN,cv::getStructuringElement(cv::MORPH_ELLIPSE,cv::Size(3,3)));
 std::vector<std::vector<cv::Point>> regions; cv::findContours(spots,regions,cv::RETR_EXTERNAL,cv::CHAIN_APPROX_SIMPLE);
 cv::circle(out.annotated,center,cvRound(radius),cv::Scalar(180,192,87),2,cv::LINE_AA);
 for(auto &c:regions){double a=cv::contourArea(c);if(a<p.min_area)continue;auto box=cv::boundingRect(c);out.regions.push_back({box.x,box.y,box.width,box.height,a});cv::rectangle(out.annotated,box,cv::Scalar(46,172,241),2,cv::LINE_AA);}
 std::sort(out.regions.begin(),out.regions.end(),[](const Region&a,const Region&b){return a.x<b.x;});
 out.warning="Demostración basada en reglas; una región sospechosa requiere revisión humana."; return out;
}
}
