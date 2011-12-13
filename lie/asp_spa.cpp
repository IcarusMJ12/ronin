// Copyright (c) 2011 Igor Kaplounenko.
// Licensed under the Open Software License version 3.0.

#include "asp_spa.h"
#include <assert.h>
using namespace std;

namespace asp_spa
{
	array<double, 2> dot(array<array<double, 2>, 2> const &matrix, array<double, 2> const &v)
	{
		array<double, 2> result;
		for(int i=0;i<2;i++)
			result[i]=inner_product<array<double, 2>::const_iterator, array<double, 2>::const_iterator, double>(matrix[i].begin(),matrix[i].end(), v.begin(),0.0);
		return result;
	}

	double dot(array<double, 2> const &other_vector, array<double, 2> const &v)
	{
		return inner_product<array<double, 2>::const_iterator, array<double, 2>::const_iterator, double>(other_vector.begin(),other_vector.end(), v.begin(),0.0);
	}

	double cross(array<double, 2> const &p1, array<double, 2> const &p2, array<double, 2> const &p3)
	{
		return (p2[0]-p1[0])*(p3[1]-p1[1])-(p2[1]-p1[1])*(p3[0]-p1[0]);
	}

	double crossVectors(Point const &v1, Point const &v2)
	{
		return v1[0]*v2[1]-v1[1]*v2[0];
	}

	void hexToRectangular(array<int, 2> const &source, array<double, 2> &destination)
	{
		array<double, 2> const source_double={static_cast<double>(source[0]),static_cast<double>(source[1])};
		destination=dot(T, source_double);
	}

	int clockwiseCompare(array<double,2> const &p1, array<double,2> const &p2)
	{
		if(p1[0]>0)
		{
			if(p2[0]<=0)
				return -1;
			if(p1[1]>p2[1])
				return -1;
			if(p1[1]==p2[1])
				return 0;
			return 1;
		}
		if(p2[0]>0)
			return 1;
		if(p2[1]>p1[1])
			return -1;
		if(p2[1]==p1[1])
			return 0;
		return 1;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator+(NumericArray<B> const &other) const
	{
		NumericArray<B> result;
		transform(this->begin(), this->end(), other.begin(), result.begin(), plus<double>());
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator-(NumericArray<B> const &other) const
	{
		NumericArray<B> result;
		transform(this->begin(), this->end(), other.begin(), result.begin(), minus<double>());
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator-() const
	{
		NumericArray<B> result=*this;
		for_each(result.begin(),result.end(),[](double x){return -x;});
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator*(NumericArray<B> const &other) const
	{
		NumericArray<B> result;
		transform(this->begin(), this->end(), other.begin(), result.begin(), multiplies<double>());
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator*(double other) const
	{
		NumericArray<B> result = *this;
		for_each(result.begin(),result.end(),[other](double x){return x*other;});
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator/(NumericArray<B> const &other) const
	{
		NumericArray<B> result;
		transform(this->begin(), this->end(), other.begin(), result.begin(), divides<double>());
		return result;
	}

	template<long unsigned int B> NumericArray<B> NumericArray<B>::operator/(double other) const
	{
		NumericArray<B> result;
		for_each(result.begin(),result.end(),[other](double x){return x/other;});
		return result;
	}

	template<long unsigned int B> NumericArray<B> const& NumericArray<B>::operator=(array<double, B> const &other)
	{
		for(int i=0;i<B;i++)
			(*this)[i]=other[i];
		return *this;
	}

	unique_ptr<RayPair> rayPairFromFF(array<int, 2> const &facing, double fov)
	{
		bool is_reflex=false;
		array<double, 2> rectangular_facing;
		array<Point, 2> left, right;
		array<array<double, 2>, 2> rotate_left, rotate_right;
		double cos_theta, sin_ltheta, sin_rtheta;

		fov=2*M_PI-fov;
		is_reflex= fov>=M_PI;
		hexToRectangular(facing, rectangular_facing);
		left[1][0]=rectangular_facing[0];
		left[1][1]=rectangular_facing[1];
		right[1][0]=rectangular_facing[0];
		right[1][1]=rectangular_facing[1];
		cos_theta=cos(-fov/2.0);
		sin_ltheta=sin(fov/2.0);
		sin_rtheta=-sin_ltheta;
		rotate_left[0][0]=rotate_right[0][0]=rotate_left[1][1]=rotate_right[1][1]=cos_theta;
		rotate_left[0][1]=rotate_right[1][0]=sin_rtheta;
		rotate_left[1][0]=rotate_right[0][1]=sin_ltheta;
		//rotate_left = {{cos_theta, sin_rtheta}, {sin_ltheta, cos_theta}};
		//rotate_right = {{cos_theta, sin_ltheta}, {sin_rtheta, cos_theta}};
		left[1]=dot(rotate_left, left[1]);
		right[1]=dot(rotate_right, right[1]);
		return unique_ptr<RayPair>(new RayPair(shared_ptr<Ray>(new Ray(left[0],left[1])), shared_ptr<Ray>(new Ray(right[0],right[1])), true));
	}

	Locus::Locus(int x, int y, bool blocks_los)
		: x(x), y(y), d_2(x*x+y*y-x*y), blocks_los(blocks_los), cover_left(0.0), cover_right(0.0)
	{
		double factor;
		array<int, 2> coord = {x, y};
		hexToRectangular(coord, this->coord);
		factor=sqrt(this->coord[0]*this->coord[0]+this->coord[1]*this->coord[1])*2.0;
		this->n[0]=-this->coord[1]/factor;
		this->n[1]=this->coord[0]/factor;
	}

	Point const Locus::getCoord() const
	{
		return this->coord;
	}

	int Locus::compare(Locus const &other) const
	{
		if(this->d_2<other.d_2)
			return -1;
		if(this->d_2>other.d_2)
			return 1;
		return clockwiseCompare(this->coord, other.coord);
	}

	bool Locus::operator<(Locus const &other) const
	{
		return this->compare(other)==-1;
	}

	int Locus::distance_2(Locus const &other) const
	{
		int dx=other.x-this->x;
		int dy=other.y-this->y;
		return dx*dx+dy*dy-dx*dy;
	}

	unique_ptr<RayPair> Locus::toRayPair() const
	{
		Point l_p2 = this->coord + this->n;
		Point r_p2 = this->coord - this->n;
		shared_ptr<Ray> left(new Ray(this->n, l_p2));
		shared_ptr<Ray> right(new Ray(-this->n, r_p2));
		return unique_ptr<RayPair>(new RayPair(left, right, false));
	}

	void Ray::fromSegment(Point const &p1, Point const &p2)
	{
		double scale_factor=0;

		this->point=p1;
		this->unit_vector=p2-p1;
		for_each(this->unit_vector.begin(), this->unit_vector.end(), [&scale_factor](double x){scale_factor+=x*x;});
		scale_factor=sqrt(scale_factor);
		this->unit_vector=this->unit_vector/scale_factor;
	}

	void Ray::fromVector(array<double,2> const &p1, array<double,2> const &p2)
	{
		this->point=p1;
		this->unit_vector=p2;
	}

	Ray::Ray()
	{
		point[0]=point[1]=unit_vector[0]=unit_vector[1]=0;
	}

	Ray::Ray(Point const &p1, Point const &p2, bool from_segment)
	{
		if(from_segment)
			this->fromSegment(p1, p2);
		else
			this->fromVector(p1, p2);
	}

	RayPair::RayPair()
		: is_reflex(false), is_world(false)
	{}

	RayPair::RayPair(shared_ptr<Ray> left, shared_ptr<Ray> right, bool is_reflex)
	{
		this->left=left;
		this->right=right;
		this->is_reflex=is_reflex;
		this->is_world=false;
	}

	int RayPair::compare(RayPair const &other) const
	{
		return clockwiseCompare(this->right->unit_vector, other.right->unit_vector);
	}

	void RayPair::mergeLocus(Locus const &locus, int line)
	{
		if(line==3)
		{
			this->is_world=true;
			return;
		}
		if(line==1)
		{
			if(cross(this->right->point, this->left->point, locus.n) <= EPSILON)
				this->is_reflex=true;
			this->left->fromSegment(locus.n, locus.coord+locus.n);
		}
		else
		{
			if(cross(this->left->point, this->right->point, -locus.n) >= -EPSILON)
				this->is_reflex=true;
			this->right->fromSegment(-locus.n, locus.coord-locus.n);
		}
	}

	shared_ptr<RayPair> RayPair::mergePairsByLocus(RayPair &lp1, int lp1_line, RayPair &lp2, int lp2_line)
	{
		shared_ptr<Ray> right, left;
		shared_ptr<RayPair> lp(new RayPair());
		bool is_reflex = lp1.is_reflex || lp2.is_reflex;
		if(lp1_line==1)
		{
			left=lp2.left;
			right=lp1.right;
			if(!is_reflex && cross(lp1.right->point, lp1.left->point, lp2.left->point)<=EPSILON)
				is_reflex=true;
		}
		else
		{
			left=lp1.left;
			right=lp2.right;
			if(!is_reflex && cross(lp2.right->point,lp2.left->point,lp1.left->point)<=EPSILON)
				is_reflex=true;
		}
		lp->left=left;
		lp->right=right;
		lp->is_reflex=is_reflex;
		return lp;
	}

	CoverTuple RayPair::calculateCover(Locus &l)
	{
		Point n;
		Point point;
		double right, left;
		if(this->is_world)
			return CoverTuple(1.0, 0);
		if(!this->is_reflex)
		{
			n=-(this->right->point+this->left->point)/2;
			if(cross(this->left->point, this->right->point, l.coord+n)<0)
				return CoverTuple(-1, 2);
		}
		right=crossVectors(this->right->unit_vector, l.coord-this->right->point*2);
		if(right>-EPSILON && right<EPSILON)
			right=0;
		else if(right>1.0-EPSILON)
			right=1;
		if(!this->is_reflex)
			if(right<0)
				return CoverTuple(-1,2);
		left=-crossVectors(this->left->unit_vector, l.coord-this->left->point*2);
		if(left>-EPSILON && left<EPSILON)
			left=0;
		else if(left>1.0-EPSILON)
			left=1;
		if(!this->is_reflex)
		{
			if(left<0)
				return CoverTuple(-1,1);
			if(left<right)
				return CoverTuple(left,1);
			if(right<1)
				return CoverTuple(right,2);
			return CoverTuple(1,0);
		}
		if(left<0 && right<0)
			return CoverTuple(-1,2);
		if(dot(this->left->unit_vector,this->right->unit_vector)<0)
		{
			if(left==1 && right==1)
				return CoverTuple(1,0);
			if(left-EPSILON>right)
				return CoverTuple(left,1);
			if(left+EPSILON>right)
			{
				Point origin, left_normal;
				origin[0]=origin[1]=0;
				left_normal[0]=-this->left->unit_vector[1];
				left_normal[1]=this->left->unit_vector[0];
				if(cross(origin, left_normal,l.coord)<0)
					return CoverTuple(left,1);
			}
			return CoverTuple(right,2);
		}
		if(left==1 || right==1)
			return CoverTuple(1,0);
		if(left>=0)
		{
			if(right>=0)
				return CoverTuple(left, right, 3);
			return CoverTuple(left, 1);
		}
		return CoverTuple(right, 2);
	}

	void FOV::processOrigin(vector<shared_ptr<Locus>> &loci, vector<shared_ptr<Locus>> &processed_loci)
	{
		shared_ptr<Locus> l;
		while(loci.size())
		{
			l=loci.back();
			if(l->d_2!=0)
				break;
			l->cover_left=l->cover_right=0.0;
			processed_loci.push_back(l);
			loci.pop_back();
		}
	}

	void FOV::processInitialFOV(vector<shared_ptr<Locus>> &loci, array<int, 2> const &facing, double fov)
	{
		unique_ptr<RayPair> raypair=rayPairFromFF(facing, fov);
		for(vector<shared_ptr<Locus>>::iterator l=loci.begin();l<=loci.end();l++)
		{
			if((*l)->x!=0 && (*l)->y!=0)
			{
				double cover_left=0, cover_right=0;
				CoverTuple ct=raypair->calculateCover(**l);
				if(ct.line==3)
				{
					cover_left=ct.cover1;
					cover_right=ct.cover2;
				}
				else if(ct.line==0)
					cover_left=cover_right=ct.cover1;
				else if(ct.line==1)
					cover_left=max(0.0,ct.cover1);
				else
					cover_right=max(0.0,ct.cover1);
				if(cover_left>0.866)
					cover_left=1.0;
				if(cover_right>0.866)
					cover_right=1.0;
				(*l)->cover_left = max((*l)->cover_left, cover_left);
				(*l)->cover_right = max((*l)->cover_right, cover_right);
			}
		}
	}

	vector<TileCover> FOV::calculateHexFOV(TileTriplet const &me, vector<TileTriplet> const &world, double fov, array<int, 2> const *facing)
	{
		vector<shared_ptr<Locus>> loci;
		shared_ptr<Locus> l;
		vector<shared_ptr<Locus>> ret;
		vector<shared_ptr<RayPair>> linepairs;
		vector<int> freshness;
		vector<TileCover> result;
		int d_2=1;
		int lp_index=0;
		for(vector<TileTriplet>::const_iterator i=world.begin();i<=world.end();i++)
			loci.push_back(shared_ptr<Locus>(new Locus(i->x-me.x, i->y-me.y, i->blocks_los)));
		sort(loci.begin(), loci.end());
		reverse(loci.begin(), loci.end());
		this->processOrigin(loci, ret);
		while(loci.size())
		{
			bool processed=false;
			int direction=0;
			int line1=-1, line2=-1;
			double cover1, cover2;
			shared_ptr<RayPair> lp1, lp2;
			l=loci.back();
			loci.pop_back();
			if(l->d_2>d_2)
			{
				d_2=l->d_2;
				lp_index=0;
				for(int i=0;i<freshness.size();i++)
					freshness[i]=0;
			}
			for(int ignored=0;ignored<linepairs.size();ignored++)
			{
				shared_ptr<RayPair> lp1=linepairs[lp_index];
				int fresh1=freshness[lp_index];
				CoverTuple cl1 = lp1->calculateCover(*l);
				CoverTuple cl2;
				if(cl1.line==3)
				{
					l->cover_right=max(cl1.cover1,0.0)*(!(fresh1&1));
					l->cover_left=max(cl1.cover2,0.0)*(!(fresh1&2));
					if(l->blocks_los && lp1->is_reflex)
						lp1->is_world=true;
					processed=true;
					break;
				}
				if(cl1.cover1==1)
				{
					if(cl1.line==2)
						l->cover_left=cl1.cover1;
					else
						l->cover_right=cl1.cover1;
					processed=true;
					break;
				}
				shared_ptr<RayPair> lp2=NULL;
				int fresh2=0;
				if(cl1.cover1>=0)
				{
					if(linepairs.size()>1)
					{
						if(cl1.line==1 && direction!=1)
						{
							lp2=linepairs[(lp_index-1)%linepairs.size()];
							fresh2=freshness[(lp_index-1)%freshness.size()];
						}
						else if(direction!=-1)
						{
							lp2=linepairs[(lp_index+1)%linepairs.size()];
							fresh2=freshness[(lp_index+1)%freshness.size()];
						}
						cl2=lp2->calculateCover(*l);
						assert(cl2.cover1>=0 && cl2.line==cl1.line);
						assert(cl2.line!=3);
					}
					if(cl1.line==2)
					{
						l->cover_right=max(cl1.cover1,0.0)*(!(fresh1&cl1.line));
						l->cover_left=max(cl2.cover1,0.0)*(!(fresh2&cl2.line));
					}
					else
					{
						l->cover_left=max(cl1.cover1,0.0)*(!(fresh1&cl1.line));
						l->cover_right=max(cl2.cover1,0.0)*(!(fresh2&cl2.line));
					}
					if(l->blocks_los)
					{
						if(cl2.cover1>=0)
						{
							shared_ptr<RayPair> lp=RayPair::mergePairsByLocus(*lp1, cl1.line, *lp2, cl2.line);
							linepairs[lp_index]=lp;
							freshness[lp_index]=fresh1|fresh2;
							if(cl1.line==1)
							{
								linepairs.erase(linepairs.begin()+((lp_index-1)%linepairs.size()));
								freshness.erase(freshness.begin()+((lp_index-1)%freshness.size()));
							}
							else
							{
								linepairs.erase(linepairs.begin()+((lp_index+1)%linepairs.size()));
								freshness.erase(freshness.begin()+((lp_index+1)%freshness.size()));
							}
							lp_index=(lp_index-1)%linepairs.size();
						}
						else
						{
							lp1->mergeLocus(*l, cl1.line);
							freshness[lp_index]+=cl1.line;
						}
					}
					processed=true;
					break;
				}
				if(!direction)
				{
					if(cl1.line==1)
						direction=-1;
					else if(cl1.line==2)
						direction=1;
				}
				else if((direction==-1 && cl1.line!=1) || (direction==1 and cl1.line!=2))
					break;
				lp_index=(lp_index+direction)%linepairs.size();
			}
			if(!processed && l->blocks_los)
			{
				linepairs.push_back(l->toRayPair());
				freshness.push_back(3);
				sort(linepairs.begin(), linepairs.end());
			}
			ret.push_back(l);
		}
		if(fov!=0&&facing!=NULL)
			this->processInitialFOV(ret, *facing, fov);
		//TODO translate yield
		for(vector<shared_ptr<Locus>>::const_iterator i=ret.begin();i<ret.end();i++)
			result.push_back(TileCover((*i)->x+me.x, (*i)->y+me.y, min((*i)->cover_right+(*i)->cover_left, 1.0),(*i)->d_2));
		return result;
	}
}

int main()
{
	unique_ptr<asp_spa::Locus> l (new asp_spa::Locus(1,1,false));
	asp_spa::Point coord = l->getCoord();
	coord[0]=10;
	coord[1]=10;
	cout<<coord[0]<<" "<<coord[1]<<endl;
	cout<<l->getCoord()[0]<<" "<<l->getCoord()[1]<<endl;
	return 0;
}
