// Copyright (c) 2011 Igor Kaplounenko.
// Licensed under the Open Software License version 3.0.

#ifndef ASP_SPA_H
#define ASP_SPA_H

#include <math.h>
#include <iostream>
#include <array>
#include <vector>
#include <algorithm>
#include <numeric>
#include <memory>

using namespace std;

namespace asp_spa
{
	const double EPSILON = 0.0000001;
	const double SQRT3_4 = sqrt(3.0/4);
	const array<array<double, 2>, 2> T = {
		-SQRT3_4, SQRT3_4,
		-0.5, -0.5 };

	template<long unsigned int B> class NumericArray : public array<double, B>
	{
		public:
			NumericArray<B> operator+(NumericArray<B> const &other) const;
			NumericArray<B> operator-(NumericArray<B> const &other) const;
			NumericArray<B> operator-() const;
			NumericArray<B> operator*(NumericArray<B> const &other) const;
			NumericArray<B> operator*(double other) const;
			NumericArray<B> operator/(NumericArray<B> const &other) const;
			NumericArray<B> operator/(double other) const;
			NumericArray<B> const& operator=(array<double, B> const &other);
	};
	typedef NumericArray<2> Point;

	int clockwiseCompare(array<double,2> const &p1, array<double,2> const &p2);
	array<double, 2> dot(array <array<double, 2>, 2> const &matrix, array<double, 2> const &v);
	double dot(array<double, 2> const &other_vector, array<double, 2> const &v);
	double cross(array<double, 2> const &p1, array<double, 2> const &p2, array<double, 2> const &p3);
	double crossVectors(Point const &v1, Point const &v2);
	void hexToRectangular(array<int, 2> const &source, array<double, 2> &destination);

	class Ray
	{
		public:
			Point point;
			Point unit_vector;
			Ray();
			Ray(Point const &p1, Point const &p2, bool from_segment=true);
			void fromSegment(Point const &p1, Point const &p2);
			void fromVector(array<double,2> const &p1, array<double,2> const &p2);
	};

	class Locus;

	class CoverTuple
	{
		public:
			double cover1, cover2;
			short line;
			CoverTuple()
				: cover1(0), cover2(0), line(0) {};
			CoverTuple(double cover, short line)
				: cover1(cover), cover2(0), line(line) {};
			CoverTuple(double cover1, double cover2, short line)
				: cover1(cover1), cover2(cover2), line(line) {};
	};

	class RayPair
	{
		public:
			shared_ptr<Ray> left;
			shared_ptr<Ray> right;
			bool is_reflex;
			bool is_world;
			RayPair();
			RayPair(shared_ptr<Ray> left, shared_ptr<Ray> right, bool is_reflex);
			int compare(RayPair const &other) const;
			void mergeLocus(Locus const &locus, int line);
			static shared_ptr<RayPair> mergePairsByLocus(RayPair &lp1, int lp1_line, RayPair &lp2, int lp2_line);
			CoverTuple calculateCover(Locus &l);
	};

	class Locus
	{
		public:
			bool blocks_los;
			Point coord, n;
			Locus(int x, int y, bool blocks_los);
			Point const getCoord() const;
			int compare(Locus const &other) const;
			bool operator<(Locus const &other) const;
			int distance_2(Locus const &other) const;
			unique_ptr<RayPair> toRayPair() const;
			const int x, y, d_2;
			double cover_left, cover_right;
	};

	class TileCover
	{
		public:
			int x, y;
			double cover;
			int d_2;
			TileCover(int x, int y, double cover, int d_2)
				: x(x), y(y), cover(cover), d_2(d_2) {};
	};

	class TileTriplet
	{
		public:
			int x, y;
			bool blocks_los;
	};

	unique_ptr<RayPair> rayPairFromFF(array<int, 2> const &facing, double fov);

	class FOV
	{
		private:
			void processOrigin(vector<shared_ptr<Locus>> &loci, vector<shared_ptr<Locus>> &processed_loci);
			void processInitialFOV(vector<shared_ptr<Locus>> &loci, array<int, 2> const &facing, double fov);
		public:
			vector<TileCover> calculateHexFOV(TileTriplet const &me, vector<TileTriplet> const &world, double fov=0, array<int, 2> const *facing=NULL);
	};

}

#endif
